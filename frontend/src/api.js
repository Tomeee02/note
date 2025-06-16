import axios from "axios";

const API_URL = "http://127.0.0.1:8000/api/";

export const getNotes = async (token) => {
  const response = await axios.get(`${API_URL}notes/`, {
    headers: { Authorization: `Token ${token}` }
  });
  return response.data;
};

export const saveNote = async (note, token) => {
  await axios.post(`${API_URL}notes/`, note, {
    headers: { Authorization: `Token ${token}` }
  });
};
