<template>
  <div>
    <h2>Elérhető dokumentumok</h2>
    <ul>
      <li v-for="doc in documents" :key="doc.id">
        <strong>{{ doc.title }}</strong> -  
        <a :href="doc.file" target="_blank">Megnyitás</a>
      </li>
    </ul>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  data() {
    return { documents: [] };
  },
  async created() {
    const token = "a2465648e3c75c6b63b715a1af3445e31aa5585a"; // Ezt majd dinamikusan kezelhetjük
    const response = await axios.get("http://127.0.0.1:8000/api/documents/", {
      headers: { Authorization: `Token ${token}` }
    });
    this.documents = response.data;
  }
};
</script>
