# 🎯 GATE-Snap | Screenshot Organizer for GATE CSE

An intelligent application designed specifically for **GATE Computer Science & Engineering (CSE)** aspirants. It allows you to paste screenshots (notes, doubts, formulas, PYQs, test series questions) directly using `Ctrl+V`, automatically extracts the text with OCR, identifies the exact GATE CSE subject and subtopic, and organizes the image into clean, dedicated subject folders.

---

## 🚀 Quick Start

You can run GATE-Snap either with **Streamlit** or with **FastAPI**:

### Option A: Launch with Streamlit (Local & Streamlit Community Cloud)
```bash
streamlit run streamlit_app.py
```
*(Running `streamlit run app.py` is also supported)*

### Option B: Launch with FastAPI
```bash
./start.sh
# or directly:
python3 -m uvicorn app:app --host 0.0.0.0 --port 8000
```
Open **[http://localhost:8000](http://localhost:8000)** (or the port shown in your terminal) in your browser.

---

## ⚡ How It Works

1. **Press `Ctrl + V` Anywhere**:
   - While viewing a video lecture, test series portal, PDF, or discussion forum, take a screenshot (`PrintScreen` or `Win+Shift+S` or `Cmd+Shift+4`).
   - Switch to the GATE-Snap tab and press `Ctrl + V`.
   - You can also drag-and-drop or click "Paste from Clipboard".

2. **Automatic Subject & Subtopic Classification**:
   - High-speed local OCR (Tesseract) extracts words, formulas, equations, and code.
   - The built-in **GATE CSE Knowledge Engine** analyzes the text against 1,000+ domain keywords, syllabus concepts, and disambiguation rules across all 12 GATE subjects.
   - Displays detected subject (with color badge & code), subtopic, confidence score, and matched keywords.

3. **Auto-Save or 1-Click Review**:
   - **Auto-Save Mode**: Toggle "Auto-Save on Paste" in the top bar to save screenshots directly into their folders in under 0.5s without any extra clicks!
   - **Manual Review Mode**: Verify the detected subject, add notes (e.g. solution tricks, formula hints), custom tags (`#PYQ2024`, `#Formula`), or change the target folder with a single click. Hit `Enter` to save.

4. **Organized Folder Structure on Your Disk**:
   All screenshots are organized in `~/gate_cse_notes/` (customizable in Settings):
   ```
   ~/gate_cse_notes/
   ├── Operating_Systems/
   │   └── OS_20261028_103408_deadlocks.png
   ├── Theory_of_Computation/
   │   └── TOC_20261028_103409_finite_automata.png
   ├── Compiler_Design/
   ├── Database_Management_Systems/
   ├── Computer_Networks/
   ├── Computer_Organization_and_Architecture/
   ├── Digital_Logic/
   ├── Data_Structures/
   ├── Algorithms/
   ├── Discrete_Mathematics/
   ├── Engineering_Mathematics/
   ├── General_Aptitude/
   └── General_Notes/
   ```

---

## 📚 Supported GATE CSE Subjects & Subtopics

| Code | Subject | Key Topics Covered |
|---|---|---|
| **OS** | Operating Systems | CPU Scheduling, Deadlocks (Banker's), Semaphores/Sync, Paging, Virtual Memory, Inodes, Disk Scheduling |
| **TOC** | Theory of Computation | DFA/NFA, Pumping Lemma, CFL/PDA, Turing Machines, Decidability, Halting Problem, Chomsky Hierarchy |
| **CD** | Compiler Design | Lexical Analysis, LL(1), LR(0)/SLR/LALR/CLR Parsers, SDT, 3-Address Code, Basic Blocks, Code Optimization |
| **DBMS** | Database Management Systems | ER Model, Relational Algebra, SQL, Functional Dependencies, BCNF/3NF, Serializability, 2PL, B+ Trees |
| **CN** | Computer Networks | Data Link (Stop&Wait, GBN, SR), CSMA/CD, IPv4/Subnetting/CIDR, Routing (Dijkstra, Distance Vector), TCP/Congestion, DNS/HTTP |
| **COA** | Computer Organization & Architecture | Addressing Modes, Instruction Pipelining, Hazards, Cache Memory Mapping (Direct/Set-Associative), AMAT, DMA |
| **DL** | Digital Logic | Boolean Algebra, K-Maps, Minimization, MUX, Decoders, Adders, Flip-Flops, Counters, IEEE 754 Floating Point |
| **DS** | Data Structures | Arrays, Stacks, Queues, Linked Lists, Trees (BST, AVL Rotations), Heaps, Hashing (Open Addressing, Chaining) |
| **ALGO** | Algorithms | Asymptotic Analysis (Big-O, Master Theorem), Divide & Conquer, Greedy (Huffman, MST), DP, Graph Algos, NP-Completeness |
| **DM** | Discrete Mathematics | Propositional & Predicate Logic, Sets & Relations, Poset/Hasse Diagram, Lattices, Combinatorics, Graph Theory (Planar, Coloring) |
| **EM** | Engineering Mathematics | Linear Algebra (Eigenvalues, Cayley-Hamilton, Rank), Calculus (Limits, Maxima/Minima), Probability (Bayes, Poisson, Normal) |
| **GA** | General Aptitude | Quantitative Aptitude, Verbal Ability, Reading Comprehension, Spatial & Analytical Reasoning |

---

## 🔍 Features

- **Global OCR Full-Text Search**: Search for formulas like `Banker's`, `Master Theorem`, `B+ Tree`, `Pumping Lemma`, or any question text to find screenshots instantly.
- **Visual Subject Explorer**: Browse folders, see screenshot counts, disk usage, and inspect full-resolution images.
- **Lightbox Inspector**: Zoom into screenshots, copy extracted OCR text with 1 click, reassign subject, or delete.
- **Preparation Distribution Dashboard**: Visual progress bars showing how your saved doubts/notes are distributed across GATE subjects.
- **Export to ZIP**: 1-click download of all organized screenshots as a zip archive.
- **Dual AI Engine**:
  - **Offline Mode (Default)**: Fast local OCR + deep GATE syllabus rule matching. Requires **zero** internet and **zero** API keys.
  - **Gemini Vision Mode (Optional)**: If you enter a Gemini API key in Settings, the app unlocks deep multimodal AI analysis for LaTeX math transcription, problem summarization, and concept explanations.

---

## 💻 Terminal & CLI Usage

You can also categorize screenshots directly from your terminal:

```bash
# Analyze screenshot currently in your system clipboard
python3 cli.py --paste

# Analyze a specific image file
python3 cli.py --image /path/to/screenshot.png

# View subject folder statistics
python3 cli.py --stats

# Dry-run analysis without saving
python3 cli.py --image /path/to/screenshot.png --dry-run
```
