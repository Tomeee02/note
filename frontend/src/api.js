import axios from "axios";

const API_URL = "http://127.0.0.1:8000/api/";

export const getBoards = async (token) => {
    const response = await axios.get(`${API_URL}boards/`, {
        headers: { Authorization: `Token ${token}` }
    });
    return response.data;
};

export const getNotes = async (boardId, token) => {
    const response = await axios.get(`${API_URL}boards/${boardId}/notes/`, {
        headers: { Authorization: `Token ${token}` }
    });
    return response.data;
};
