<template>
  <div>
    <h2>Dokumentum feltöltése</h2>
    <input type="text" v-model="title" placeholder="Dokumentum címe" />
    <input type="file" @change="handleFileUpload" />
    <button @click="upload">Feltöltés</button>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  data() {
    return { file: null, title: "" };
  },
  methods: {
    handleFileUpload(event) {
      this.file = event.target.files[0];
    },
    async upload() {
      if (!this.file || !this.title) return alert("Adj meg címet és fájlt!");
      
      const formData = new FormData();
      formData.append("title", this.title);
      formData.append("file", this.file);
      
      const token = "a2465648e3c75c6b63b715a1af3445e31aa5585a"; // Ezt később cseréljük ki dinamikus autentikációval
      await axios.post("http://127.0.0.1:8000/api/documents/", formData, {
        headers: { Authorization: `Token ${token}` }
      });

      alert("Feltöltés sikeres!");
    }
  }
};
</script>
