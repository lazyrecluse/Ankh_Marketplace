export const back_end_endpoint = () => {
    return process.env.REACT_APP_BACKEND_ENDPOINT || "http://localhost:8000";
}