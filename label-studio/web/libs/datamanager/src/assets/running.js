import Running24 from "!!url-loader!./Loading.gif";
import Running24x2 from "!!url-loader!./Loading.gif";
import Running48 from "!!url-loader!./Loading.gif";
import Running48x2 from "!!url-loader!./Loading.gif";
import Running64 from "!!url-loader!./Loading.gif";
import Running64x2 from "!!url-loader!./Loading.gif";
import Running from "!!url-loader!./Loading.gif";

const sizes = {
  full: {
    x1: Running,
    x2: Running,
  },
  24: {
    x1: Running24,
    x2: Running24x2,
  },
  48: {
    x1: Running48,
    x2: Running48x2,
  },
  64: {
    x1: Running64,
    x2: Running64x2,
  },
};

export default sizes;
