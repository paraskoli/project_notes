"""
GATE CSE Subject Classifier and OCR Engine.
Extracts text from screenshots and categorizes them into official GATE CSE subjects.
Supports both fast offline OCR + Rule-based NLP and optional Gemini AI Vision.
"""

import os
import re
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from PIL import Image
import pytesseract

logger = logging.getLogger(__name__)

# Complete GATE CSE Subjects Taxonomy
GATE_SUBJECTS = {
    "Operating_Systems": {
        "name": "Operating Systems",
        "code": "OS",
        "color": "#3B82F6", # Blue
        "icon": "desktop-outline",
        "description": "Processes, Threads, CPU Scheduling, Deadlock, Memory Management, Virtual Memory, File Systems, Disk Scheduling",
        "subtopics": {
            "Processes & Threads": ["process", "thread", "pcb", "tcb", "context switch", "fork", "exec", "ipc", "shared memory", "message passing"],
            "CPU Scheduling": ["scheduling", "fcfs", "sjf", "srtf", "round robin", "priority scheduling", "turnaround time", "waiting time", "response time", "gantt chart", "burst time", "quantum"],
            "Synchronization & Semaphores": ["synchronization", "critical section", "mutual exclusion", "semaphore", "mutex", "peterson", "test and set", "monitor", "dining philosopher", "reader writer", "producer consumer", "bounded buffer", "race condition"],
            "Deadlocks": ["deadlock", "banker", "resource allocation graph", "rag", "safe state", "unsafe state", "prevention", "avoidance", "detection", "circular wait", "hold and wait"],
            "Memory Management & Paging": ["paging", "page table", "tlb", "translation lookaside", "inverted page table", "segmentation", "logical address", "physical address", "frame", "internal fragmentation", "external fragmentation"],
            "Virtual Memory": ["virtual memory", "page fault", "page replacement", "fifo", "lru", "optimal page", "belady", "belady's anomaly", "thrashing", "working set"],
            "File Systems & Disk Scheduling": ["file system", "inode", "disk scheduling", "sstf", "scan", "c-scan", "look", "c-look", "seek time", "rotational latency"]
        },
        "strong_keywords": [
            "operating system", "semaphores", "deadlock", "banker's algorithm", "bankers algorithm", 
            "page fault", "belady's anomaly", "beladys anomaly", "tlb miss", "tlb hit", "page replacement", 
            "round robin", "gantt chart", "turnaround time", "critical section", "dining philosophers",
            "readers writers", "shortest remaining time first", "c-scan", "c-look", "multilevel queue",
            "inode", "virtual memory", "demand paging", "thrashing", "context switch"
        ],
        "keywords": [
            "process", "processes", "thread", "threads", "semaphore", "mutex", "fork()", "pthread",
            "scheduling", "fcfs", "sjf", "srtf", "quantum", "burst time", "arrival time", "preemptive",
            "non-preemptive", "deadlocks", "safe state", "allocation matrix", "need matrix", "max matrix",
            "paging", "segmentation", "page table", "frame size", "page size", "tlb", "lru", "mru",
            "disk scheduling", "sstf", "seek time", "rotational delay", "transfer rate", "fragmentation"
        ]
    },

    "Theory_of_Computation": {
        "name": "Theory of Computation",
        "code": "TOC",
        "color": "#8B5CF6", # Violet / Purple
        "icon": "shapes-outline",
        "description": "Automata, DFA, NFA, Regular Expressions, Grammars, CFG, PDA, Turing Machines, Decidability, Halting Problem",
        "subtopics": {
            "Finite Automata & Regular Languages": ["dfa", "nfa", "regular expression", "regular language", "epsilon transition", "subset construction", "myhill nerode", "pumping lemma for regular", "state minimization"],
            "Context Free Languages & Pushdown Automata": ["cfg", "context free", "cfl", "pda", "pushdown", "chomsky normal form", "cnf", "gnf", "ambiguous grammar", "pumping lemma for cfl"],
            "Turing Machines & Decidability": ["turing machine", "recursively enumerable", "recursive language", "decidable", "undecidable", "halting problem", "rice's theorem", "rices theorem", "pcp", "post correspondence", "reduction"],
            "Chomsky Hierarchy": ["chomsky hierarchy", "regular", "context-free", "context-sensitive", "unrestricted", "type 0", "type 1", "type 2", "type 3"]
        },
        "strong_keywords": [
            "theory of computation", "dfa", "nfa", "turing machine", "pumping lemma", "halting problem",
            "decidable", "undecidable", "context-free language", "context free grammar", "pushdown automata",
            "myhill-nerode", "myhill nerode", "rice's theorem", "rices theorem", "chomsky normal form",
            "regular expression", "regular expressions", "post correspondence problem", "cfg", "pda",
            "accepts the string", "state diagram", "transition table", "start state", "accept state", "final state"
        ],
        "keywords": [
            "automata", "automaton", "alphabet", "sigma", "epsilon", "closure property", "closure properties",
            "deterministic", "non-deterministic", "nondeterministic", "ambiguity", "unambiguous",
            "recursively enumerable", "enumerable", "complement of language", "kleene star", "kleene closure",
            "tape alphabet", "blank symbol", "transition function", "delta(", "derivation tree", "parse tree"
        ]
    },

    "Compiler_Design": {
        "name": "Compiler Design",
        "code": "CD",
        "color": "#EC4899", # Pink
        "icon": "code-slash-outline",
        "description": "Lexical Analysis, Parsers (LL, LR, LALR), Syntax Directed Translation, Intermediate Code, Code Optimization, Register Allocation",
        "subtopics": {
            "Lexical Analysis": ["lexical", "lexer", "token", "lexeme", "pattern", "flex", "lex", "symbol table"],
            "Syntax Analysis & Parsing": ["parser", "parsing", "ll(1)", "ll(k)", "lr(0)", "slr(1)", "lalr(1)", "clr(1)", "first and follow", "first set", "follow set", "shift reduce", "reduce reduce", "handle pruning", "parsing table", "predictive parser"],
            "Syntax Directed Translation (SDT)": ["sdt", "syntax directed", "s-attributed", "l-attributed", "synthesized attribute", "inherited attribute", "annotated parse tree"],
            "Intermediate Code Generation": ["intermediate code", "three address code", "3-address code", "quadruples", "triples", "indirect triples", "dag", "directed acyclic graph", "postfix notation"],
            "Code Optimization & Run-Time": ["code optimization", "basic block", "flow graph", "dead code", "common subexpression", "loop invariant", "strength reduction", "register allocation", "liveness", "activation record"]
        },
        "strong_keywords": [
            "compiler design", "first and follow", "first(", "follow(", "shift-reduce", "shift reduce",
            "reduce-reduce", "lalr", "slr(1)", "clr(1)", "ll(1)", "syntax directed translation",
            "s-attributed", "l-attributed", "synthesized attribute", "inherited attribute",
            "three address code", "3 address code", "intermediate code", "basic blocks", "flow graph",
            "register allocation", "lexical analyzer", "activation record"
        ],
        "keywords": [
            "compiler", "parser", "parsing", "grammar", "token", "tokens", "lexeme", "lexemes",
            "predictive parsing", "handle", "viable prefix", "lr parsing", "ll parser", "dag",
            "common subexpression", "loop unrolling", "dead code elimination", "peephole optimization",
            "target code", "static single assignment", "ssa", "quadruple", "triple", "symbol table"
        ]
    },

    "Database_Management_Systems": {
        "name": "Database Management Systems (DBMS)",
        "code": "DBMS",
        "color": "#10B981", # Emerald Green
        "icon": "server-outline",
        "description": "ER Model, Relational Algebra, SQL, Normalization, Transactions, Concurrency Control, Serializability, Indexing, B/B+ Trees",
        "subtopics": {
            "ER Modeling & Relational Model": ["entity", "relationship", "er diagram", "weak entity", "relational model", "cardinality", "primary key", "foreign key", "candidate key", "super key"],
            "Relational Algebra & SQL": ["relational algebra", "tuple relational calculus", "trc", "drc", "select", "project", "natural join", "cross product", "division operator", "sql", "group by", "having", "nested query", "outer join"],
            "Normalization & Functional Dependencies": ["functional dependency", "closure of attribute", "attribute closure", "canonical cover", "minimal cover", "1nf", "2nf", "3nf", "bcnf", "lossless join", "dependency preservation", "multivalued dependency"],
            "Transactions & Concurrency Control": ["transaction", "acid", "serializability", "conflict serializable", "view serializable", "precedence graph", "recoverability", "cascadeless", "strict schedule", "two phase locking", "2pl", "strict 2pl", "rigorous 2pl", "timestamp ordering", "deadlock in dbms"],
            "Indexing & B/B+ Trees": ["indexing", "b-tree", "b+ tree", "b plus tree", "dense index", "sparse index", "primary index", "clustering index", "secondary index", "order of b-tree", "order of b+ tree", "index block", "data pointer"]
        },
        "strong_keywords": [
            "database management", "relational algebra", "sql query", "bcnf", "3nf", "2nf", "functional dependency",
            "conflict serializable", "view serializable", "precedence graph", "two phase locking", "2pl",
            "b+ tree", "b plus tree", "b-tree", "canonical cover", "lossless decomposition", "dependency preserving",
            "candidate key", "super key", "foreign key", "acid properties", "cascadeless", "recoverable schedule"
        ],
        "keywords": [
            "database", "dbms", "relation", "tuple", "tuples", "attribute", "attributes", "table", "schema",
            "select count", "group by", "having clause", "outer join", "natural join", "inner join",
            "closure", "normal form", "normalization", "multivalued dependency", "transaction", "commit", "abort",
            "dirty read", "unrepeatable read", "phantom read", "timestamp", "clustered index", "order p"
        ]
    },

    "Computer_Networks": {
        "name": "Computer Networks",
        "code": "CN",
        "color": "#F59E0B", # Amber / Orange
        "icon": "globe-outline",
        "description": "OSI/TCP-IP Layers, Framing, Error/Flow Control, CSMA/CD, IP Addressing, Subnetting, Routing, TCP/UDP, Congestion Control",
        "subtopics": {
            "Data Link Layer & Error/Flow Control": ["framing", "crc", "cyclic redundancy", "checksum", "hamming code", "stop and wait", "go back n", "gbn", "selective repeat", "efficiency of protocol", "transmission delay", "propagation delay", "bandwidth delay product"],
            "Medium Access Control (MAC)": ["csma/cd", "csma/ca", "aloha", "pure aloha", "slotted aloha", "binary exponential backoff", "ethernet", "collision domain", "minimum frame length"],
            "Network Layer & IP Addressing": ["ipv4", "ipv6", "ip address", "subnetting", "subnet mask", "cidr", "supernetting", "classful", "classless", "fragmentation", "mtu", "offset", "more fragments", "nat", "arp", "rarp", "icmp"],
            "Routing Protocols": ["routing", "distance vector", "count to infinity", "link state", "dijkstra routing", "ospf", "rip", "bgp", "bellman ford routing", "autonomous system"],
            "Transport Layer & Congestion Control": ["tcp", "udp", "three-way handshake", "syn ack", "tcp header", "seq number", "acknowledgement number", "flow control", "congestion control", "slow start", "congestion avoidance", "fast retransmit", "fast recovery", "threshold", "cwnd", "rtt"],
            "Application Layer & Security": ["dns", "http", "https", "ftp", "smtp", "pop3", "imap", "dhcp", "socket", "port number", "symmetric encryption", "asymmetric", "rsa", "digital signature"]
        },
        "strong_keywords": [
            "computer networks", "stop and wait", "go-back-n", "go back n", "selective repeat", "sliding window",
            "csma/cd", "csma cd", "subnet mask", "cidr", "ipv4 header", "ipv6 header", "three way handshake",
            "slow start", "congestion window", "cwnd", "cyclic redundancy check", "crc generator", "hamming distance",
            "distance vector routing", "count to infinity", "link state routing", "ospf", "transmission delay",
            "propagation delay", "bandwidth delay product", "minimum frame size"
        ],
        "keywords": [
            "network", "packet", "packets", "frame", "router", "switch", "ip address", "subnet", "broadcast address",
            "network address", "fragmentation", "offset", "datagram", "tcp", "udp", "socket", "port", "dns",
            "http", "congestion", "throughput", "efficiency", "bit rate", "baud rate", "aloha", "ethernet", "mtu"
        ]
    },

    "Computer_Organization_and_Architecture": {
        "name": "Computer Organization & Architecture (COA)",
        "code": "COA",
        "color": "#06B6D4", # Cyan
        "icon": "hardware-chip-outline",
        "description": "Addressing Modes, Instruction Pipelining, Hazards, Cache Memory, Mapping, Virtual Memory/TLB, Interrupts, DMA",
        "subtopics": {
            "Machine Instructions & Addressing": ["instruction format", "opcode", "addressing mode", "direct addressing", "indirect addressing", "indexed", "base register", "pc relative", "auto increment", "instruction cycle"],
            "ALU & Data Path": ["data path", "control unit", "hardwired control", "microprogrammed", "horizontal microcode", "vertical microcode", "alu", "booth algorithm", "restoring division"],
            "Instruction Pipelining": ["pipelining", "pipeline", "pipeline stages", "throughput", "speedup", "hazard", "data hazard", "raw hazard", "war hazard", "waw hazard", "structural hazard", "control hazard", "branch penalty", "operand forwarding", "branch prediction", "stall cycles"],
            "Memory Hierarchy & Cache": ["cache", "cache memory", "cache mapping", "direct mapped", "fully associative", "set associative", "tag bits", "index bits", "block offset", "hit ratio", "miss penalty", "amat", "average memory access time", "write through", "write back", "write allocate", "l1 cache", "l2 cache"],
            "I/O Interfaces & DMA": ["i/o interface", "interrupt", "vectored interrupt", "dma", "direct memory access", "cycle stealing", "burst mode", "daisy chaining", "programmed i/o", "memory mapped i/o", "isolated i/o"]
        },
        "strong_keywords": [
            "computer organization", "computer architecture", "addressing mode", "addressing modes",
            "instruction pipelining", "pipeline hazard", "operand forwarding", "raw hazard", "war hazard",
            "direct mapped cache", "set associative cache", "fully associative cache", "cache hit ratio",
            "average memory access time", "amat", "write through", "write back", "hardwired control",
            "microprogrammed control", "cycle stealing", "vectored interrupt", "branch penalty"
        ],
        "keywords": [
            "pipeline", "pipelining", "cache", "tag bits", "block size", "cache size", "word offset",
            "speedup", "throughput", "microinstruction", "control memory", "clock cycle", "cpi", "mips",
            "dma", "interrupt", "bus", "alu", "register transfer", "accumulator", "program counter", "instruction register"
        ]
    },

    "Digital_Logic": {
        "name": "Digital Logic",
        "code": "DL",
        "color": "#EAB308", # Yellow / Amber
        "icon": "git-network-outline",
        "description": "Boolean Algebra, K-Maps, Combinational Circuits, Multiplexers, Sequential Circuits, Flip-Flops, Counters, Number Systems",
        "subtopics": {
            "Boolean Algebra & Logic Gates": ["boolean algebra", "logic gate", "nand", "nor", "universal gate", "xor", "xnor", "de morgan", "sop", "pos", "canonical", "minterm", "maxterm", "duality"],
            "Minimization & K-Maps": ["karnaugh map", "k-map", "kmap", "prime implicant", "essential prime implicant", "epi", "dont care", "don't care", "quine mccluskey"],
            "Combinational Circuits": ["multiplexer", "mux", "demultiplexer", "demux", "decoder", "encoder", "priority encoder", "half adder", "full adder", "ripple carry adder", "carry lookahead adder"],
            "Sequential Circuits & Flip-Flops": ["sequential circuit", "flip flop", "flip-flop", "latch", "sr flip flop", "jk flip flop", "d flip flop", "t flip flop", "race around", "master slave", "excitation table", "characteristic equation"],
            "Registers & Counters": ["counter", "asynchronous counter", "ripple counter", "synchronous counter", "mod-n counter", "mod counter", "ring counter", "johnson counter", "shift register", "siso", "sipo", "piso", "pipo"],
            "Number Systems & Floating Point": ["number system", "binary", "hexadecimal", "octal", "1's complement", "2's complement", "ieee 754", "floating point", "mantissa", "exponent", "bias"]
        },
        "strong_keywords": [
            "digital logic", "k-map", "karnaugh map", "essential prime implicant", "prime implicants",
            "multiplexer", "mux", "demultiplexer", "full adder", "half adder", "carry lookahead",
            "flip-flop", "flip flop", "jk flip-flop", "master-slave flip flop", "race-around condition",
            "mod-", "ripple counter", "ring counter", "johnson counter", "synchronous counter",
            "2's complement", "two's complement", "ieee 754", "floating point representation"
        ],
        "keywords": [
            "logic gate", "nand", "nor", "boolean", "minterm", "maxterm", "dont care", "sop", "pos",
            "decoder", "encoder", "latch", "excitation", "state table", "state transition", "propagation delay",
            "shift register", "overflow", "excess-3", "bcd", "binary to gray", "gray code"
        ]
    },

    "Data_Structures": {
        "name": "Data Structures",
        "code": "DS",
        "color": "#14B8A6", # Teal
        "icon": "layers-outline",
        "description": "Arrays, Stacks, Queues, Linked Lists, Trees, Binary Search Trees, AVL Trees, Heaps, Hashing, Graphs representation",
        "subtopics": {
            "Arrays & Matrices": ["array", "row major", "column major", "sparse matrix", "multi-dimensional array"],
            "Stacks & Queues": ["stack", "queue", "circular queue", "deque", "infix to postfix", "postfix evaluation", "prefix", "parenthesis matching"],
            "Linked Lists": ["linked list", "singly linked", "doubly linked", "circular linked", "floyd cycle detection", "cycle detection"],
            "Trees & Binary Search Trees (BST)": ["binary tree", "bst", "binary search tree", "inorder", "preorder", "postorder", "level order", "height of tree", "complete binary tree", "full binary tree", "strictly binary tree"],
            "Balanced Trees": ["avl tree", "avl rotation", "balance factor", "red-black tree", "b-tree", "b+ tree"],
            "Heaps & Priority Queues": ["heap", "min heap", "max heap", "heapify", "build heap", "priority queue", "heap sort"],
            "Hashing": ["hashing", "hash table", "hash function", "collision resolution", "open addressing", "linear probing", "quadratic probing", "double hashing", "chaining"]
        },
        "strong_keywords": [
            "data structure", "data structures", "binary search tree", "avl tree", "balance factor",
            "inorder traversal", "preorder traversal", "postorder traversal", "level order traversal",
            "min heap", "max heap", "heapify", "linear probing", "quadratic probing", "double hashing",
            "circular queue", "row-major order", "column-major order", "doubly linked list"
        ],
        "keywords": [
            "stack", "queue", "push", "pop", "enqueue", "dequeue", "linked list", "node", "tree", "root",
            "leaf node", "internal node", "depth of tree", "height", "bst", "heap", "priority queue",
            "hash table", "hash", "collision", "chaining", "adjacency matrix", "adjacency list"
        ]
    },

    "Algorithms": {
        "name": "Algorithms",
        "code": "ALGO",
        "color": "#EF4444", # Red
        "icon": "analytics-outline",
        "description": "Asymptotic Analysis, Master Theorem, Divide & Conquer, Greedy, Dynamic Programming, Graph Algorithms, NP-Completeness",
        "subtopics": {
            "Asymptotic Analysis & Recurrences": ["asymptotic", "big-o", "big-theta", "big-omega", "master theorem", "recurrence relation", "substitution method", "recursion tree", "time complexity", "space complexity"],
            "Divide and Conquer": ["divide and conquer", "merge sort", "quick sort", "binary search", "strassen", "median of medians"],
            "Greedy Algorithms": ["greedy", "fractional knapsack", "huffman coding", "job sequencing", "activity selection", "prims", "kruskals", "minimum spanning tree", "mst"],
            "Dynamic Programming": ["dynamic programming", "dp", "0/1 knapsack", "longest common subsequence", "lcs", "matrix chain multiplication", "mcm", "bellman ford dp", "floyd warshall", "optimal substructure", "overlapping subproblems"],
            "Graph Algorithms": ["graph algorithm", "bfs", "dfs", "dijkstra", "bellman ford", "floyd warshall", "topological sort", "strongly connected components", "scc", "kosaraju", "tarjan", "bipartite matching"],
            "NP-Completeness": ["np-complete", "np-hard", "np complete", "np hard", "p vs np", "polynomial reduction", "circuit sat", "3-sat", "vertex cover", "clique problem", "hamiltonian cycle problem", "tsp"]
        },
        "strong_keywords": [
            "algorithm", "algorithms", "master theorem", "recurrence relation", "time complexity", "asymptotic notation",
            "merge sort", "quick sort", "huffman coding", "fractional knapsack", "matrix chain multiplication",
            "longest common subsequence", "dijkstra's algorithm", "dijkstras algorithm", "bellman-ford",
            "floyd-warshall", "topological sort", "strongly connected components", "minimum spanning tree",
            "kruskal's algorithm", "prim's algorithm", "np-complete", "np-hard", "3-sat"
        ],
        "keywords": [
            "complexity", "o(n)", "theta(n)", "omega(n)", "greedy", "dynamic programming", "divide and conquer",
            "shortest path", "mst", "bfs", "dfs", "reduction", "polynomial time", "partition", "pivot",
            "worst case", "average case", "best case", "amortized analysis"
        ]
    },

    "Discrete_Mathematics": {
        "name": "Discrete Mathematics",
        "code": "DM",
        "color": "#6366F1", # Indigo
        "icon": "infinite-outline",
        "description": "Propositional & Predicate Logic, Sets, Relations, Functions, Lattices, Combinatorics, Groups, Graph Theory",
        "subtopics": {
            "Mathematical Logic": ["propositional logic", "predicate logic", "tautology", "contradiction", "contingency", "inference rule", "modus ponens", "universal quantifier", "existential quantifier", "validity"],
            "Sets, Relations & Functions": ["set theory", "power set", "cartesian product", "relation", "reflexive", "symmetric", "transitive", "equivalence relation", "partial order", "poset", "hasse diagram", "lattice", "injective", "surjective", "bijective", "pigeonhole principle"],
            "Combinatorics & Counting": ["combinatorics", "permutation", "combination", "generating function", "inclusion exclusion", "recurrence relations dm"],
            "Group Theory": ["group theory", "group", "subgroup", "abelian group", "monoid", "semigroup", "cyclic group", "lagrange theorem"],
            "Graph Theory (Discrete Math)": ["graph theory", "planar graph", "eulers formula", "euler formula", "chromatic number", "graph coloring", "isomorphism", "handshaking theorem", "eulerian path", "eulerian circuit", "hamiltonian graph", "bipartite graph"]
        },
        "strong_keywords": [
            "discrete mathematics", "propositional logic", "predicate logic", "tautology", "modus ponens",
            "equivalence relation", "hasse diagram", "poset", "partially ordered set", "lattice",
            "pigeonhole principle", "generating function", "inclusion-exclusion", "group theory", "abelian group",
            "planar graph", "euler's formula v-e+f", "chromatic number", "graph coloring", "handshaking lemma",
            "isomorphic graphs", "regular graph", "bipartite"
        ],
        "keywords": [
            "logic", "truth table", "quantifier", "for all", "there exists", "set", "subset", "reflexive",
            "symmetric", "transitive", "injective", "surjective", "bijective", "combinations", "permutations",
            "order of group", "cyclic", "subgroup", "edges", "vertices", "faces", "planar", "chromatic"
        ]
    },

    "Engineering_Mathematics": {
        "name": "Engineering Mathematics",
        "code": "EM",
        "color": "#0284C7", # Sky Blue
        "icon": "calculator-outline",
        "description": "Linear Algebra, Eigenvalues/Eigenvectors, Matrix Rank, Calculus, Maxima/Minima, Probability & Statistics",
        "subtopics": {
            "Linear Algebra": ["linear algebra", "matrix", "determinant", "eigenvalue", "eigenvalues", "eigenvector", "eigenvectors", "characteristic equation", "rank of matrix", "system of linear equations", "cayley hamilton", "orthogonal matrix", "nullity", "basis", "dimension"],
            "Calculus": ["calculus", "limit", "limits", "continuity", "differentiability", "l'hopital", "maxima", "minima", "mean value theorem", "rolles theorem", "lagrange mean value", "taylor series", "definite integral", "partial derivative"],
            "Probability & Statistics": ["probability", "conditional probability", "bayes theorem", "random variable", "discrete random variable", "continuous random variable", "expectation", "variance", "standard deviation", "poisson distribution", "binomial distribution", "normal distribution", "uniform distribution", "exponential distribution", "covariance"]
        },
        "strong_keywords": [
            "engineering mathematics", "eigenvalues", "eigenvectors", "eigenvalue", "eigenvector",
            "cayley-hamilton", "cayley hamilton", "rank of matrix", "system of linear equations", "ax=b",
            "bayes' theorem", "bayes theorem", "conditional probability", "poisson distribution",
            "binomial distribution", "normal distribution", "probability density function", "pdf", "pmf",
            "l'hopital's rule", "l hopital", "mean value theorem", "maxima and minima"
        ],
        "keywords": [
            "matrix", "matrices", "determinant", "inverse of matrix", "null space", "row echelon",
            "derivative", "integral", "integration", "limit", "continuity", "variance", "standard deviation",
            "expected value", "random variable", "coin tossed", "dice rolled", "distribution"
        ]
    },

    "General_Aptitude": {
        "name": "General Aptitude",
        "code": "GA",
        "color": "#F97316", # Bright Orange
        "icon": "bulb-outline",
        "description": "Verbal Ability, Reading Comprehension, Quantitative Aptitude, Numerical Ability, Spatial Aptitude",
        "subtopics": {
            "Verbal Ability": ["verbal ability", "grammar", "sentence completion", "reading comprehension", "vocabulary", "synonym", "antonym", "analogy", "spelling", "preposition"],
            "Quantitative Aptitude": ["quantitative aptitude", "percentage", "profit and loss", "ratio and proportion", "speed distance time", "work and time", "simple interest", "compound interest", "mixture and alligation", "series", "data interpretation"],
            "Spatial & Analytical Aptitude": ["spatial aptitude", "paper folding", "pattern completion", "blood relations", "seating arrangement", "direction sense", "syllogism", "statement and conclusion"]
        },
        "strong_keywords": [
            "general aptitude", "sentence completion", "reading comprehension", "profit and loss",
            "speed time and distance", "simple interest", "compound interest", "blood relation",
            "seating arrangement", "syllogism", "most appropriate word to fill in the blank",
            "passage given below", "select the word that is opposite", "select the word that is similar"
        ],
        "keywords": [
            "aptitude", "percentage", "ratio", "train travels", "speed of", "invested", "sum of money",
            "analogy", "grammatically correct", "conclusion follows", "pattern", "folding"
        ]
    }
}


class GATEClassifier:
    """Analyzes text/screenshots and classifies them into GATE CSE subjects."""

    def __init__(self, gemini_api_key: Optional[str] = None):
        self.gemini_api_key = gemini_api_key or os.getenv("GEMINI_API_KEY")

    def set_api_key(self, api_key: str):
        self.gemini_api_key = api_key.strip() if api_key else None

    def ocr_image(self, image: Image.Image) -> str:
        """Extract text from PIL image using Tesseract OCR with preprocessing."""
        try:
            # Convert RGBA or Palette to RGB
            if image.mode in ("RGBA", "P"):
                image = image.convert("RGB")
            
            # Tesseract OCR extraction
            text = pytesseract.image_to_string(image, config='--oem 3 --psm 6')
            if not text.strip():
                # Fallback to general PSM 3 if psm 6 produced nothing
                text = pytesseract.image_to_string(image, config='--oem 3 --psm 3')
            return text.strip()
        except Exception as e:
            logger.error(f"Tesseract OCR failed: {e}")
            return ""

    def classify_text(self, text: str) -> Dict[str, Any]:
        """Classify extracted text into GATE CSE subjects using rule/keyword scoring."""
        if not text or len(text.strip()) < 3:
            return self._fallback_response(text, "No recognizable text found in screenshot.")

        cleaned_text = text.lower()
        # Normalize punctuation and whitespaces
        cleaned_text = re.sub(r'[\r\n\t]+', ' ', cleaned_text)
        
        subject_scores: Dict[str, float] = {k: 0.0 for k in GATE_SUBJECTS}
        matched_details: Dict[str, List[str]] = {k: [] for k in GATE_SUBJECTS}
        detected_subtopics: Dict[str, List[str]] = {k: [] for k in GATE_SUBJECTS}

        for sub_id, data in GATE_SUBJECTS.items():
            # 1. Match Strong Keywords (Weight: 4.0)
            for kw in data["strong_keywords"]:
                pattern = r'\b' + re.escape(kw.lower()) + r'\b'
                matches = len(re.findall(pattern, cleaned_text))
                if matches > 0:
                    score_gain = matches * 4.5
                    subject_scores[sub_id] += score_gain
                    matched_details[sub_id].append(f"{kw} (+{score_gain:.1f})")

            # 2. Match Standard Keywords (Weight: 1.5)
            for kw in data["keywords"]:
                pattern = r'\b' + re.escape(kw.lower()) + r'\b'
                matches = len(re.findall(pattern, cleaned_text))
                if matches > 0:
                    score_gain = matches * 1.5
                    subject_scores[sub_id] += score_gain
                    if len(matched_details[sub_id]) < 10:
                        matched_details[sub_id].append(f"{kw}")

            # 3. Match Specific Subtopics
            for subtopic_name, sub_kws in data["subtopics"].items():
                for skw in sub_kws:
                    if re.search(r'\b' + re.escape(skw.lower()) + r'\b', cleaned_text):
                        subject_scores[sub_id] += 2.0
                        if subtopic_name not in detected_subtopics[sub_id]:
                            detected_subtopics[sub_id].append(subtopic_name)

        # Disambiguation heuristics
        self._apply_gate_disambiguation(cleaned_text, subject_scores)

        # Sort subjects by score descending
        ranked = sorted(subject_scores.items(), key=lambda x: x[1], reverse=True)
        top_subject, top_score = ranked[0]

        total_score = sum(subject_scores.values())
        if top_score <= 0:
            return self._fallback_response(text, "No distinct GATE CSE keywords detected.")

        # Calculate confidence percentage (capped at 99%)
        second_score = ranked[1][1] if len(ranked) > 1 else 0
        diff = top_score - second_score
        
        # Base confidence calculation
        confidence = min(98.0, max(45.0, 50.0 + (top_score * 3.5) + (diff * 2.0)))
        if confidence > 96 and second_score > 0.8 * top_score:
            confidence = 82.0 # Close contest

        subtopic_str = detected_subtopics[top_subject][0] if detected_subtopics[top_subject] else "General Topics"
        sub_info = GATE_SUBJECTS[top_subject]

        alternatives = []
        for alt_id, alt_score in ranked[1:4]:
            if alt_score > 0:
                alternatives.append({
                    "subject_id": alt_id,
                    "name": GATE_SUBJECTS[alt_id]["name"],
                    "code": GATE_SUBJECTS[alt_id]["code"],
                    "score": round(alt_score, 1)
                })

        # Suggest clean filename
        slug_subtopic = re.sub(r'[^a-zA-Z0-9]+', '_', subtopic_str).strip('_').lower()
        if len(slug_subtopic) > 25:
            slug_subtopic = slug_subtopic[:25]

        return {
            "success": True,
            "subject_id": top_subject,
            "subject_name": sub_info["name"],
            "subject_code": sub_info["code"],
            "folder_name": top_subject,
            "color": sub_info["color"],
            "confidence": round(confidence, 1),
            "subtopic": subtopic_str,
            "matched_keywords": matched_details[top_subject][:8],
            "alternatives": alternatives,
            "ocr_text": text,
            "slug_subtopic": slug_subtopic,
            "source": "local_nlp"
        }

    def _apply_gate_disambiguation(self, text: str, scores: Dict[str, float]):
        """Specialized disambiguation logic for overlapping GATE concepts."""
        # Dijkstra: Can be Algorithms or Computer Networks
        if "dijkstra" in text:
            if any(w in text for w in ["routing", "router", "link state", "packet", "network", "ospf"]):
                scores["Computer_Networks"] += 4.0
            else:
                scores["Algorithms"] += 4.0

        # Bellman-Ford: Can be Algorithms or Computer Networks
        if "bellman" in text or "distance vector" in text:
            if any(w in text for w in ["routing", "count to infinity", "hop", "router"]):
                scores["Computer_Networks"] += 4.0
            else:
                scores["Algorithms"] += 4.0

        # B-Tree / B+ Tree: Can be DBMS (indexing) or Data Structures
        if "b+ tree" in text or "b tree" in text or "b-tree" in text:
            if any(w in text for w in ["database", "disk", "block pointer", "record pointer", "clustered", "order of leaf", "index"]):
                scores["Database_Management_Systems"] += 5.0
            else:
                scores["Data_Structures"] += 3.0

        # Paging / Virtual Memory: Can be OS or COA
        if "tlb" in text or "virtual address" in text:
            if any(w in text for w in ["cache", "amat", "memory hierarchy", "direct mapped", "tag bits"]):
                scores["Computer_Organization_and_Architecture"] += 4.0
            else:
                scores["Operating_Systems"] += 4.0

        # Graph Theory: Can be Discrete Mathematics or Algorithms
        if "planar" in text or "chromatic" in text or "euler's formula" in text or "handshaking" in text:
            scores["Discrete_Mathematics"] += 6.0

        # Propositional Logic vs Digital Logic:
        if any(w in text for w in ["tautology", "modus ponens", "quantifier", "predicate"]):
            scores["Discrete_Mathematics"] += 6.0
        if any(w in text for w in ["k-map", "karnaugh", "multiplexer", "flip flop", "mux", "counter"]):
            scores["Digital_Logic"] += 6.0

        # Compiler Design vs Theory of Computation:
        # Grammars appear in both, but parsing / first & follow / LL / LR / SDT belongs to Compiler Design
        if any(w in text for w in ["first and follow", "first(", "follow(", "ll(1)", "lr(0)", "slr", "lalr", "clr", "shift reduce", "shift-reduce", "predictive parse", "predictive parsing", "parsing table", "syntax directed", "sdt", "s-attributed", "l-attributed", "three address code", "intermediate code", "basic block", "flow graph"]):
            scores["Compiler_Design"] += 12.0


    def classify_with_gemini(self, image: Image.Image, fallback_text: str = "") -> Optional[Dict[str, Any]]:
        """Optional deep classification using Gemini Vision API."""
        if not self.gemini_api_key:
            return None

        try:
            import google.generativeai as genai
            genai.configure(api_key=self.gemini_api_key)

            # Build list of valid subject keys
            valid_keys = list(GATE_SUBJECTS.keys())

            system_instruction = f"""
            You are an expert exam analyzer for the GATE Computer Science and Engineering (CSE) examination in India.
            You will be shown a screenshot of notes, questions, formulas, diagrams, or slides.
            Categorize the content strictly into ONE of the following official GATE CSE subject keys:
            {json.dumps(valid_keys, indent=2)}

            Output strictly JSON matching this structure:
            {{
                "subject_id": "<one of the valid subject keys>",
                "subtopic": "<specific subtopic name, e.g. LR(1) Parsers, Banker's Algorithm, Master Theorem, Eigenvalues>",
                "confidence": <integer between 60 and 99>,
                "question_or_formula_summary": "<brief 1-sentence description of the screenshot content>",
                "latex_or_text": "<transcribed question / formula in clean markdown/LaTeX if visible>"
            }}
            """

            model = genai.GenerativeModel(
                model_name="gemini-1.5-flash",
                generation_config={"response_mime_type": "application/json"}
            )

            prompt = "Analyze this GATE CSE screenshot and determine its exact subject and subtopic."
            response = model.generate_content([prompt, image])
            data = json.loads(response.text)

            subject_id = data.get("subject_id")
            if subject_id in GATE_SUBJECTS:
                sub_info = GATE_SUBJECTS[subject_id]
                subtopic = data.get("subtopic", "General")
                slug_subtopic = re.sub(r'[^a-zA-Z0-9]+', '_', subtopic).strip('_').lower()[:25]
                
                return {
                    "success": True,
                    "subject_id": subject_id,
                    "subject_name": sub_info["name"],
                    "subject_code": sub_info["code"],
                    "folder_name": subject_id,
                    "color": sub_info["color"],
                    "confidence": float(data.get("confidence", 95.0)),
                    "subtopic": subtopic,
                    "matched_keywords": ["Gemini Vision AI Analysis"],
                    "alternatives": [],
                    "ocr_text": data.get("latex_or_text", fallback_text),
                    "summary": data.get("question_or_formula_summary", ""),
                    "slug_subtopic": slug_subtopic,
                    "source": "gemini_ai"
                }
        except Exception as e:
            logger.warning(f"Gemini API call failed or rate-limited: {e}. Falling back to local OCR.")
            return None

    def analyze_image(self, image: Image.Image, use_ai: bool = True) -> Dict[str, Any]:
        """Main entry point: analyzes image using Gemini Vision or local OCR + NLP."""
        # 1. First run fast local OCR so we have extracted text regardless
        extracted_text = self.ocr_image(image)

        # 2. If AI is requested and API key is present, try Gemini
        if use_ai and self.gemini_api_key:
            ai_result = self.classify_with_gemini(image, fallback_text=extracted_text)
            if ai_result:
                if not ai_result.get("ocr_text"):
                    ai_result["ocr_text"] = extracted_text
                return ai_result

        # 3. Use robust local rule & keyword classifier
        local_result = self.classify_text(extracted_text)
        return local_result

    def _fallback_response(self, text: str, reason: str) -> Dict[str, Any]:
        default_sub = "General_Notes"
        return {
            "success": True,
            "subject_id": default_sub,
            "subject_name": "General CSE & Uncategorized",
            "subject_code": "GEN",
            "folder_name": default_sub,
            "color": "#64748B",
            "confidence": 35.0,
            "subtopic": "Uncategorized",
            "matched_keywords": [],
            "alternatives": [
                {"subject_id": k, "name": GATE_SUBJECTS[k]["name"], "code": GATE_SUBJECTS[k]["code"]}
                for k in ["Operating_Systems", "Algorithms", "Computer_Networks"]
            ],
            "ocr_text": text,
            "slug_subtopic": "uncategorized",
            "reason": reason,
            "source": "fallback"
        }
