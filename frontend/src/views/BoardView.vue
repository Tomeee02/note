<template>
  <nav class="topbar">
    <div class="topbar-left">{{ board.title }}</div>
    <div class="topbar-right">
      <button class="settings-btn" @click="openSettings">⚙️</button>
    </div>
  </nav>
  <div style="display: flex;">
    <div class="toolbar">
      <div>
        <div class="template-icon" title="Új jegyzet" @click="createNote()">📝</div>
        <div class="template-icon" title="Új board" @click="createBoard()">📁</div>
        <div class="template-icon" title="Új dokumentum" @click="createDocument()">📄</div>
      </div>
      <div v-if="selectedNote" class="color-tools">
        <input type="color" v-model="selectedNote.background_color" @change="updateNoteStyle(selectedNote)" title="Háttérszín" />
        <input type="color" v-model="selectedNote.text_color" @change="updateNoteStyle(selectedNote)" title="Betűszín" />
      </div>
      <div v-if="selectedBoard" class="emoji-panel">
        <h4>📁 Ikon kiválasztása</h4>
        <div class="emoji-grid">
          <span
            v-for="icon in availableIcons"
            :key="icon"
            :class="{ selected: icon === selectedBoard.emoji }"
            @click="updateBoardIcon(selectedBoard, icon)"
          >
            {{ icon }}
          </span>
        </div>
      </div>
    </div>
    <!-- Main -->
    <div style="flex: 1; padding-left: 16px;">
      <section>
        <div v-for="note in notes" :key="note.id" class="sticky-note" draggable="true" @dragstart="onNoteDragStart(note)" :style="{ left: note.position_x + 'px', top: note.position_y + 'px', background: note.background_color, color: note.text_color, width: note.width + 'px', height: note.height + 'px', borderColor: note.background_color}" @mousedown="startDrag(note, $event)" @click="selectedNote = note">
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
          @dblclick="$router.push(`/boards/${child.id}`)"
          @dragover.prevent
          @click="selectedBoard = child"
          @drop="handleNoteDropOnBoard($event, child)">
          <div class="emoji">{{ child.emoji }}</div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'

const route = useRoute()
const router = useRouter()

// 📚 Állapotok
const board = ref({})
const notes = ref([])
const children = ref([])
const selectedNote = ref(null)
const selectedBoard = ref(null)

// 🎨 Színek + ikonok
const availableIcons = [
  "📄", "📝", "📦", "📁", "⚙️", "✅", "🧠", "🚀", "🎯",
  "🗃️", "🗂️", "🗄️", "💡", "✏️", "🖋️", "📒", "🧾", "📌", "📅",
  "📈", "⏳", "🔁", "🕒", "☑️", "🔒", "📥", "📤", "🎨", "🌈", "🧱", "🧩", "🔧", "🧰", "🖥️"
]

// 📌 Snap to grid
const gridSize = 20
const snapToGrid = (value) => Math.round(value / gridSize) * gridSize

// 📍 Emoji menü jobb klikkre
const emojiMenu = ref({
  visible: false,
  x: 0,
  y: 0,
  board: null
})
onMounted(async () => {
  const boardId = route.params.id
  const boardRes = await axios.get(`http://127.0.0.1:8000/api/boards/${boardId}/`)
  board.value = boardRes.data

  const notesRes = await axios.get('http://127.0.0.1:8000/api/notes/')
  notes.value = notesRes.data
    .filter(n => n.board === board.value.id)
    .map(n => ({ ...n, editing: false }))

  const boardsRes = await axios.get('http://127.0.0.1:8000/api/boards/')
  children.value = boardsRes.data.filter(b => b.parent === board.value.id)

  window.addEventListener('keydown', handleKeyDown)
})

onBeforeUnmount(() => {
  window.removeEventListener('keydown', handleKeyDown)
})

const handleKeyDown = async (e) => {
  if (e.key === 'Delete' && selectedNote.value) {
    const confirmDelete = confirm('Biztosan törlöd a kijelölt jegyzetet?')
    if (!confirmDelete) return
    await axios.delete(`http://127.0.0.1:8000/api/notes/${selectedNote.value.id}/`)
    notes.value = notes.value.filter(n => n.id !== selectedNote.value.id)
    selectedNote.value = null
  }
}

const createNote = async () => {
  const res = await axios.post('http://127.0.0.1:8000/api/notes/', {
    board: board.value.id,
    content: 'Új jegyzet',
    position_x: snapToGrid(100),
    position_y: snapToGrid(100),
    background_color: '#fff8b3',
    text_color: '#000',
    width: 160,
    height: 100
  })
  notes.value.push({ ...res.data, editing: true })
}

const createBoard = async () => {
  const res = await axios.post('http://127.0.0.1:8000/api/boards/', {
    title: 'Új board',
    parent: board.value.id || null,
    user: board.value.user,
    emoji: "📁",
    position_x: snapToGrid(200),
    position_y: snapToGrid(150)
  })
  children.value.push(res.data)
}

const createDocument = async () => {
  await axios.post('http://127.0.0.1:8000/api/documents/', {
    board: board.value.id,
    title: 'Új dokumentum',
    content: ''
  })
  alert('📄 Új dokumentum létrehozva!')
}

const updateNoteStyle = async (note) => {
  await axios.patch(`http://127.0.0.1:8000/api/notes/${note.id}/`, {
    background_color: note.background_color,
    text_color: note.text_color
  })
}

const updateBoardIcon = async (boardObj, icon) => {
  boardObj.emoji = icon
  await axios.patch(`http://127.0.0.1:8000/api/boards/${boardObj.id}/`, {
    emoji: icon
  })
}
// 🎯 Jegyzet mozgatás (egérrel)
const draggedNote = ref(null)
const offset = { x: 0, y: 0 }

const onNoteDragStart = (note) => {
  draggedNote.value = note
}

const startDrag = (note, e) => {
  draggedNote.value = note
  offset.x = e.clientX - note.position_x
  offset.y = e.clientY - note.position_y
  window.addEventListener('mousemove', onDrag)
  window.addEventListener('mouseup', stopDrag)
}

const onDrag = (e) => {
  if (!draggedNote.value) return
  draggedNote.value.position_x = snapToGrid(e.clientX - offset.x)
  draggedNote.value.position_y = snapToGrid(e.clientY - offset.y)
}

const stopDrag = async () => {
  if (!draggedNote.value) return
  await axios.patch(`http://127.0.0.1:8000/api/notes/${draggedNote.value.id}/`, {
    position_x: draggedNote.value.position_x,
    position_y: draggedNote.value.position_y
  })
  draggedNote.value = null
  window.removeEventListener('mousemove', onDrag)
  window.removeEventListener('mouseup', stopDrag)
}

// 📁 Board mozgatás (ugyanez boardokra)
let draggedBoard = null
let boardOffset = { x: 0, y: 0 }

const startBoardDrag = (child, e) => {
  draggedBoard = child
  boardOffset.x = e.clientX - child.position_x
  boardOffset.y = e.clientY - child.position_y
  window.addEventListener('mousemove', onBoardDrag)
  window.addEventListener('mouseup', stopBoardDrag)
}

const onBoardDrag = (e) => {
  if (!draggedBoard) return
  draggedBoard.position_x = snapToGrid(e.clientX - boardOffset.x)
  draggedBoard.position_y = snapToGrid(e.clientY - boardOffset.y)
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
// 🧲 Jegyzet áthelyezése másik board-ra
const handleNoteDropOnBoard = async (e, targetBoard) => {
  if (!draggedNote.value || !targetBoard) return
  await axios.patch(`http://127.0.0.1:8000/api/notes/${draggedNote.value.id}/`, {
    board: targetBoard.id
  })
  notes.value = notes.value.filter(n => n.id !== draggedNote.value.id)
  draggedNote.value = null
}

// 🖊️ Szerkesztés dupla kattintásra
const finishEdit = async (note) => {
  note.editing = false
  await axios.patch(`http://127.0.0.1:8000/api/notes/${note.id}/`, {
    content: note.content
  })
}

// ↔️ Jegyzet méretezése
const startResize = (note, e) => {
  const startX = e.clientX
  const startY = e.clientY
  const startWidth = note.width || 160
  const startHeight = note.height || 100

  const onMouseMove = (ev) => {
    note.width = Math.max(100, startWidth + (ev.clientX - startX))
    note.height = Math.max(80, startHeight + (ev.clientY - startY))
  }

  const onMouseUp = async () => {
    window.removeEventListener('mousemove', onMouseMove)
    window.removeEventListener('mouseup', onMouseUp)
    await axios.patch(`http://127.0.0.1:8000/api/notes/${note.id}/`, {
      width: note.width,
      height: note.height
    })
  }

  window.addEventListener('mousemove', onMouseMove)
  window.addEventListener('mouseup', onMouseUp)
}

// 🎯 Emoji panel jobb klikkre
const openEmojiMenu = (e, boardObj) => {
  emojiMenu.value = {
    visible: true,
    x: e.clientX,
    y: e.clientY,
    board: boardObj
  }
}

const selectBoardIcon = async (icon) => {
  const boardToUpdate = emojiMenu.value.board
  if (!boardToUpdate) return
  boardToUpdate.emoji = icon
  await axios.patch(`http://127.0.0.1:8000/api/boards/${boardToUpdate.id}/`, {
    emoji: icon
  })
  emojiMenu.value.visible = false
}

// ⌨️ Bezárás ESC-re
window.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    emojiMenu.value.visible = false
  }
})

const openSettings = () => {
  alert('⚙️ Beállítások még nincsenek – de dolgozhatunk rajta 😄')
}
</script>



 <style scoped> 
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
.emoji-panel {
  position: fixed;
  top: 60px;
  right: 16px;
  background: #fff;
  border: 1px solid #ccc;
  border-radius: 10px;
  padding: 12px 16px;
  width: 180px;
  box-shadow: 0 4px 8px rgba(0,0,0,0.1);
  z-index: 1000;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.emoji-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.emoji-grid span {
  font-size: 24px;
  cursor: pointer;
  padding: 6px;
  border-radius: 6px;
  transition: background 0.2s;
}

.emoji-grid span.selected {
  background: #f0f0f0;
  box-shadow: inset 0 0 0 2px #666;
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
     display: flex;
    flex-direction: column;
}
 .emoji {
     font-size: 36px;
     text-align: center;
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