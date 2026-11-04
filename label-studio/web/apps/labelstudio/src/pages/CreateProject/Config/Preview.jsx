// import { useCallback, useEffect, useMemo, useRef, useState } from "react";
// import { Spinner } from "../../../components";
// import { cn } from "../../../utils/bem";
// import "./Config.scss";
// import { EMPTY_CONFIG } from "./Template";
// import { API_CONFIG } from "../../../config/ApiConfig";
// import { useAPI } from "../../../providers/ApiProvider";

// const configClass = cn("configure");

// // Lazy load Label Studio with a single promise to avoid multiple loads
// // and enable as early as possible to load the dependencies once this component is mounted for the first time
// let dependencies;
// const loadDependencies = async () => {
//   if (!dependencies) {
//     dependencies = import("@humansignal/editor");
//   }
//   return dependencies;
// };

// export const Preview = ({ config, data, error, loading, project }) => {
//   // @see comment about dependencies above
//   loadDependencies();

//   const [storeReady, setStoreReady] = useState(false);
//   const lsf = useRef(null);
//   const rootRef = useRef();
//   const api = useAPI();
//   const projectRef = useRef(project);
//   projectRef.current = project;

//   const currentTask = useMemo(() => {
//     return {
//       id: 1,
//       annotations: [],
//       predictions: [],
//       data,
//     };
//   }, [data]);

//   /**
//    * Proxy urls to presign them if storage is connected
//    * @param {*} _ LS instance
//    * @param {string} url http/https are not proxied and returned as is
//    */
//   const onPresignUrlForProject = async (_, url) => {
//     const parsedUrl = new URL(url);

//     // return same url if http(s)
//     if (["http:", "https:"].includes(parsedUrl.protocol)) return url;

//     const projectId = projectRef.current.id;

//     const fileuri = btoa(url);

//     return api.api.createUrl(API_CONFIG.endpoints.presignUrlForProject, { projectId, fileuri }).url;
//   };

//   const currentConfig = useMemo(() => {
//     // empty string causes error in LSF
//     return config ?? EMPTY_CONFIG;
//   }, [config]);

//   const initLabelStudio = useCallback(async (config, task) => {
//     // wait for dependencies to load, the promise is resolved only once
//     // and is started when the component is mounted for the first time
//     await loadDependencies();

//     if (lsf.current || !task.data) return;

//     try {
//       lsf.current = new window.LabelStudio(rootRef.current, {
//         config,
//         task,
//         interfaces: ["side-column"],
//         // with SharedStore we should use more late event
//         onStorageInitialized(LS) {
//           LS.settings.bottomSidePanel = true;

//           const initAnnotation = () => {
//             const as = LS.annotationStore;
//             const c = as.createAnnotation();

//             as.selectAnnotation(c.id);
//             setStoreReady(true);
//           };

//           // and even then we need to wait a little even after the store is initialized
//           setTimeout(initAnnotation);
//         },
//       });

//       lsf.current.on("presignUrlForProject", onPresignUrlForProject);
//     } catch (err) {
//       console.error(err);
//     }
//   }, []);

//   useEffect(() => {
//     const opacity = loading || error ? 0.6 : 1;
//     // to avoid rerenders and data loss we do it this way

//     document.getElementById("label-studio").style.opacity = opacity;
//   }, [loading, error]);

//   useEffect(() => {
//     initLabelStudio(currentConfig, currentTask).then(() => {
//       if (storeReady && lsf.current?.store) {
//         const store = lsf.current.store;

//         store.resetState();
//         store.assignTask(currentTask);
//         store.assignConfig(currentConfig);
//         store.initializeStore(currentTask);

//         const c = store.annotationStore.addAnnotation({
//           userGenerate: true,
//         });

//         store.annotationStore.selectAnnotation(c.id);
//         console.log("LSF updated");
//       }
//     });
//   }, [currentConfig, currentTask, storeReady]);

//   useEffect(() => {
//     return () => {
//       if (lsf.current) {
//         console.info("Destroying LSF");
//         lsf.current.destroy();
//         lsf.current = null;
//       }
//     };
//   }, []);

//   return (
//     <div className={configClass.elem("preview")}>
//       <h3>UI Preview</h3>
//       {error && (
//         <div className={configClass.elem("preview-error")}>
//           <h2>
//             {error.detail} {error.id}
//           </h2>
//           {error.validation_errors?.non_field_errors?.map?.((err) => (
//             <p key={err}>{err}</p>
//           ))}
//           {error.validation_errors?.label_config?.map?.((err) => (
//             <p key={err}>{err}</p>
//           ))}
//           {error.validation_errors?.map?.((err) => (
//             <p key={err}>{err}</p>
//           ))}
//         </div>
//       )}
//       {!data && loading && <Spinner style={{ width: "100%", height: "50vh" }} />}
//       <div id="label-studio" className={configClass.elem("preview-ui")} ref={rootRef} />
//     </div>
//   );
// };
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Spinner } from "../../../components";
import { cn } from "../../../utils/bem";
import "./Config.scss";
import { EMPTY_CONFIG } from "./Template";
import { API_CONFIG } from "../../../config/ApiConfig";
import { useAPI } from "../../../providers/ApiProvider";

const configClass = cn("configure");

let dependencies;
const loadDependencies = async () => {
  if (!dependencies) {
    dependencies = import("@humansignal/editor");
  }
  return dependencies;
};

export const Preview = ({ config, data, error, loading, project }) => {
  loadDependencies();
  const [storeReady, setStoreReady] = useState(false);
  const lsf = useRef(null);
  const rootRef = useRef();
  const api = useAPI();
  const projectRef = useRef(project);
  projectRef.current = project;

  // New state for auto-fix tracking
  const [autoFixed, setAutoFixed] = useState(false);

  /**
   * Automatically add missing labels from model to config
   */
  const fixMissingLabels = useCallback(async (currentConfig) => {
    try {
      // Get model labels from ML backend
      const modelInfo = await api.callApi("mlInfo", {
        params: { pk: projectRef.current.id },
      });

      if (!modelInfo?.labels?.length) return currentConfig;

      // Parse current config
      const parser = new DOMParser();
      const xmlDoc = parser.parseFromString(currentConfig, "application/xml");
      const serializer = new XMLSerializer();

      // Find all Label tags
      const labelTags = xmlDoc.getElementsByTagName("Label");
      const existingLabels = Array.from(labelTags).map(el => el.getAttribute("value"));

      // Find missing labels
      const missingLabels = modelInfo.labels.filter(
        label => !existingLabels.includes(label)
      );

      if (missingLabels.length === 0) return currentConfig;

      // Add missing labels to the first Labels control found
      const labelsControls = xmlDoc.getElementsByTagName("Labels");
      if (labelsControls.length > 0) {
        const firstControl = labelsControls[0];
        const palette = ["#FF6B6B", "#4ECDC4", "#45B7D1", "#FFA07A", "#98D8C8"];

        missingLabels.forEach((label, index) => {
          const newLabel = xmlDoc.createElement("Label");
          newLabel.setAttribute("value", label);
          newLabel.setAttribute("background", palette[index % palette.length]);
          firstControl.appendChild(newLabel);
        });

        const updatedConfig = serializer.serializeToString(xmlDoc);
        setAutoFixed(true); // Track that we auto-fixed labels
        return updatedConfig;
      }
    } catch (e) {
      console.error("Failed to auto-fix labels:", e);
    }
    return currentConfig;
  }, [api]);

  const currentTask = useMemo(() => ({
    id: 1,
    annotations: [],
    predictions: [],
    data,
  }), [data]);

  const onPresignUrlForProject = async (_, url) => {
    const parsedUrl = new URL(url);
    if (["http:", "https:"].includes(parsedUrl.protocol)) return url;

    const projectId = projectRef.current.id;
    const fileuri = btoa(url);
    return api.api.createUrl(API_CONFIG.endpoints.presignUrlForProject, { projectId, fileuri }).url;
  };

  const initLabelStudio = useCallback(async (config, task) => {
    await loadDependencies();
    if (lsf.current || !task.data) return;

    try {
      // First try to fix any label mismatches
      const fixedConfig = await fixMissingLabels(config);

      lsf.current = new window.LabelStudio(rootRef.current, {
        config: fixedConfig,
        task,
        interfaces: ["side-column"],
        onStorageInitialized(LS) {
          LS.settings.bottomSidePanel = true;
          const initAnnotation = () => {
            const as = LS.annotationStore;
            const c = as.createAnnotation();
            as.selectAnnotation(c.id);
            setStoreReady(true);
          };
          setTimeout(initAnnotation);
        },
      });

      lsf.current.on("presignUrlForProject", onPresignUrlForProject);
    } catch (err) {
      console.error(err);
    }
  }, [fixMissingLabels]);

  useEffect(() => {
    const opacity = loading || error ? 0.6 : 1;
    document.getElementById("label-studio").style.opacity = opacity;
  }, [loading, error]);

  useEffect(() => {
    initLabelStudio(config, currentTask);
  }, [config, currentTask, initLabelStudio]);

  return (
    <div className={configClass.elem("preview")}>
      <h3>UI Preview</h3>
      {autoFixed && (
        <div className={configClass.elem("auto-fix-notice")}>
          <span>✓ Added missing labels automatically</span>
        </div>
      )}
      {error && (
        <div className={configClass.elem("preview-error")}>
          <h2>{error.detail} {error.id}</h2>
          {error.validation_errors?.non_field_errors?.map?.((err) => (
            <p key={err}>{err}</p>
          ))}
        </div>
      )}
      {!data && loading && <Spinner style={{ width: "100%", height: "50vh" }} />}
      <div id="label-studio" className={configClass.elem("preview-ui")} ref={rootRef} />
    </div>
  );
};