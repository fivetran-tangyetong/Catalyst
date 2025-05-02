declare namespace NodeJS {
    interface ProcessEnv {
      REACT_APP_API_URL: string;
      REACT_APP_APIFY_TOKEN: string;
      REACT_APP_VAPI_API_KEY: string;
      REACT_APP_ARCADE_KEY: string;
      // add any other REACT_APP_* vars here
    }
  }