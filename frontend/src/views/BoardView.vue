<template>
  <nav class="topbar">
    <div class="topbar-left">{{ board.title }}</div>
    <div class="topbar-right">
      <button class="settings-btn" @click="openSettings">⚙️</button>
    </div>
  </nav>
  <div style="display: flex;">
    <div class="toolbar">
      <div class="toolbar">
    <div class="template-icon" title="Új jegyzet" @click="createNote()">📝</div>
    <div class="template-icon" title="Új board" @click="createBoard()">📁</div>
    <div class="template-icon" title="Új dokumentum" @click="createDocument()">📄</div>
  </div>

    <div v-if="selectedNote" class="color-tools">
      <input type="color" v-model="selectedNote.background_color" @change="updateNoteStyle(selectedNote)" title="Háttérszín" />
    </div>
    </div>
    <!-- Main -->
    <div style="flex: 1; padding-left: 16px;">
      <section>
        <div v-for="note in notes" :key="note.id" class="sticky-note" :style="{ left: note.position_x + 'px', top: note.position_y + 'px', background: note.background_color, color: note.text_color, width: note.width + 'px', height: note.height + 'px', borderColor: note.background_color}" @mousedown="startDrag(note, $event)" @click="selectedNote = note">
          <div v-if="!note.editing" @dblclick="note.editing = true">
            {{ note.content }}
          </div>
          <!-- Szerkesztés textarea-ban -->
          <textarea
            v-else
            v-model="note.content"
            @blur="finishEdit(note)"
            @keyup.enter.exact.prevent="finishEdit(note)"
            class="note-editor"
          />
          <!-- Sizing corner -->
          <div class="resizer" @mousedown.stop="startResize(note, $event)" ></div>
        </div>
        <div 
          v-for="child in children" 
          :key="child.id" 
          class="board-card" 
          :style="{ left: child.position_x + 'px', top: child.position_y + 'px', width: '65px', height: '65px' }" 
          @mousedown="startBoardDrag(child, $event)" 
          @dblclick="$router.push(`/boards/${child.id}`)">
          <div class="emoji">{{ child.emoji }}</div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import axios from 'axios'

const availableIcons = ["📄", "📝", "📦", "📁", "⚙️", "✅", "🧠", "🚀", "🎯"]
const selectedIcon = ref("📄")
const route = useRoute()                 // URL paramétereket kapunk
const board = ref({})                   // Reaktív objektum a board adatnak
const notes = ref([])                   // Jegyzetek tömbje
const children = ref([])                // Alboardok tömbje

let draggedBoard = null
let boardOffsetX = 0
let boardOffsetY = 0

const startBoardDrag = (child, event) => {
  draggedBoard = child
  boardOffsetX = event.clientX - child.position_x
  boardOffsetY = event.clientY - child.position_y

  window.addEventListener('mousemove', onBoardDrag)
  window.addEventListener('mouseup', stopBoardDrag)
}

const finishEdit = async (note) => {
  note.editing = false
  await axios.patch(`http://127.0.0.1:8000/api/notes/${note.id}/`, {
    content: note.content
  })
}


const onBoardDrag = (event) => {
  if (!draggedBoard) return
  draggedBoard.position_x = event.clientX - boardOffsetX
  draggedBoard.position_y = event.clientY - boardOffsetY
}

const stopBoardDrag = async () => {
  if (!draggedBoard) return
  await axios.patch(`http://127.0.0.1:8000/api/boards/${draggedBoard.id}/`, {
    position_x: draggedBoard.position_x,
    position_y: draggedBoard.position_y
  })
  draggedBoard = null
  window.removeEventListener('mousemove', onBoardDrag)
  window.removeEventListener('mouseup', stopBoardDrag)
}

onMounted(async () => {
  const boardId = route.params.id       // pl. "1" ha az URL /boards/1
  const boardRes = await axios.get(`http://127.0.0.1:8000/api/boards/${boardId}/`)
  board.value = boardRes.data

  console.log('Kapott board:', board.value) 

  const notesRes = await axios.get('http://127.0.0.1:8000/api/notes/')
  notes.value = notesRes.data
  .filter(n => n.board === board.value.id)
  .map(n => ({ ...n, editing: false }))


  const boardsRes = await axios.get('http://127.0.0.1:8000/api/boards/')
  children.value = boardsRes.data.filter(b => b.parent === board.value.id)

  console.log('Route param id:', route.params.id)
  console.log('Kapott board:', board.value)
  console.log('Jegyzetek:', notes.value)
  console.log('Gyerek boardok:', children.value)
})

const createNote = async () => {
  if (!board.value.id) return
  const res = await axios.post('http://127.0.0.1:8000/api/notes/', {
    board: board.value.id,
    content: 'Új jegyzet',
    position_x: 100,
    position_y: 100
  })
  notes.value.push(res.data)
}

const createBoard = async () => {
  const res = await axios.post('http://127.0.0.1:8000/api/boards/', {
    title: 'Új board',
    parent: board.value.id || null,
    user: board.value.user,  // vagy helyette egy fix user azonosító
    emoji: selectedIcon.value
  })
  children.value.push(res.data)
}

const createDocument = async () => {
  const res = await axios.post('http://127.0.0.1:8000/api/documents/', {
    title: 'Új dokumentum',
    content: '',
    board: board.value.id
  })
  alert('📄 Új dokumentum létrehozva!')
}
let draggedNote = null
let offsetX = 0
let offsetY = 0

const startDrag = (note, event) => {
  draggedNote = note
  offsetX = event.clientX - note.position_x
  offsetY = event.clientY - note.position_y
  window.addEventListener('mousemove', onDrag)
  window.addEventListener('mouseup', stopDrag)
}

const onDrag = (event) => {
  if (!draggedNote) return
  draggedNote.position_x = event.clientX - offsetX
  draggedNote.position_y = event.clientY - offsetY
}

const stopDrag = async () => {
  if (!draggedNote) return

  // Mentés az API-ba (opcionális)
  await axios.patch(`http://127.0.0.1:8000/api/notes/${draggedNote.id}/`, {
    position_x: draggedNote.position_x,
    position_y: draggedNote.position_y
  })

  draggedNote = null
  window.removeEventListener('mousemove', onDrag)
  window.removeEventListener('mouseup', stopDrag)
}
  const selectedNote = ref(null)

const updateNoteStyle = async (note) => {
  await axios.patch(`http://127.0.0.1:8000/api/notes/${note.id}/`, {
    background_color: note.background_color,
    text_color: note.text_color
  })
}
const openSettings = () => {
  alert('Beállítások még nem készültek el – de dolgozhatunk rajta 😉')
}
const startResize = (note, event) => {
  const startX = event.clientX
  const startY = event.clientY
  const startWidth = note.width || 160
  const startHeight = note.height || 100

  const onMouseMove = (e) => {
    const newWidth = Math.max(100, startWidth + (e.clientX - startX))
    const newHeight = Math.max(80, startHeight + (e.clientY - startY))
    note.width = newWidth
    note.height = newHeight
  }

  const onMouseUp = async () => {
    window.removeEventListener('mousemove', onMouseMove)
    window.removeEventListener('mouseup', onMouseUp)

    // Mentés backendre
    await axios.patch(`http://127.0.0.1:8000/api/notes/${note.id}/`, {
      width: note.width,
      height: note.height
    })
  }

  window.addEventListener('mousemove', onMouseMove)
  window.addEventListener('mouseup', onMouseUp)
}
</script> <style scoped> 
.sticky-note {
     position: absolute;
     min-width: 100px;
     min-height: 80px;
     padding: 8px;
     border-radius: 6px;
     box-shadow: 2px 2px 6px rgba(0, 0, 0, 0.15);
     cursor: grab;
     user-select: none;
     overflow: hidden;
     border: 1px solid transparent;
}
 .resizer {
     position: absolute;
     width: 16px;
     height: 16px;
     right: 2px;
     bottom: 2px;
     background: transparent;
     border-right: 2px solid rgba(0, 0, 0, 0.3);
     border-bottom: 2px solid rgba(0, 0, 0, 0.3);
     box-sizing: border-box;
     cursor: nwse-resize;
     pointer-events: auto;
}
 .topbar {
     position: fixed;
     top: 0;
     left: 0;
     right: 0;
     height: 40px;
     background: #fdfdfd;
     border-bottom: 1px solid #ccc;
     padding: 0 16px;
     display: flex;
     align-items: center;
     justify-content: space-between;
     font-weight: bold;
     font-size: 15px;
     z-index: 1000;
}
 .topbar-left {
     color: #333;
}
.note-editor {
  width: 100%;
  height: 100%;
  border: none;
  outline: none;
  resize: none;
  font: inherit;
  background: transparent;
  padding: 0;
  box-sizing: border-box;
}

 .topbar-right {
     display: flex;
     align-items: center;
}
 .settings-btn {
     background: none;
     border: none;
     font-size: 20px;
     cursor: pointer;
     padding: 4px;
     transition: transform 0.2s;
}
 .settings-btn:hover {
     transform: rotate(20deg);
}
 .board-area {
     flex: 1;
     position: relative;
     height: calc(100vh - 40px);
     margin-top: 40px;
    /* Ezzel elkerülöd az átfedést */
     overflow: hidden;
     margin-left: 48px;
}
 .toolbar {
     position: fixed;
     top: 40px;
     left: 0;
     width: 48px;
     height: calc(100vh - 40px);
     background: #f8f8f8;
     padding: 8px 4px;
     border-right: 1px solid #ccc;
     display: flex;
     flex-direction: column;
     align-items: center;
     gap: 12px;
     z-index: 999;
}
 .toolbar button {
     background: none;
     border: none;
     font-size: 20px;
     cursor: pointer;
     transition: transform 0.2s;
}
 .toolbar button:hover {
     transform: scale(1.2);
}
 .color-tools {
     display: flex;
     flex-direction: column;
     gap: 6px;
     margin-top: 8px;
}
 .color-tools input[type="color"] {
     width: 28px;
     height: 28px;
     border: none;
     border-radius: 4px;
     padding: 0;
     cursor: pointer;
     box-shadow: 0 0 3px rgba(0, 0, 0, 0.2);
}
 .board-card {
     position: absolute;
     border-radius: 8px;
     background: #f8f8f8;
     border: 1px solid #ccc;
     box-shadow: 1px 1px 5px rgba(0, 0, 0, 0.1);
     text-align: center;
     display: flex;
     align-items: center;
     justify-content: center;
     font-size: 36px;
     cursor: grab;
     user-select: none;
}
 .emoji {
     font-size: 36px;
     text-align: center;
     margin-top: 18px;
}
 .template-icon {
     font-size: 28px;
     cursor: grab;
     margin: 10px 0;
     transition: transform 0.2s;
}
 .template-icon:hover {
     transform: scale(1.2);
}
 </style> 