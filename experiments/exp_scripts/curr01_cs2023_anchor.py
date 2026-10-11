"""CURR01: Anchor the academic reference profile to ACM/IEEE-CS/AAAI CS2023.

Rationale : The academic skill profile (hf_job_skill_set top-500) is a dataset
            proxy for curricula. CURR01 validates it against the authoritative
            CS2023 curriculum Body of Knowledge (ACM/IEEE-CS/AAAI Joint Task
            Force, 2024): are the Knowledge-Area topics that CS programs are
            expected to teach semantically present in the reference profile?

Inputs : hf_job_skill_set.csv (academic reference) + embedded CS2023 topic
         list (2197 topics, 17 Knowledge Areas; extracted from the official
         Body of Knowledge PDF via datasets/cs2023/extract_topics.py).
Outputs: metrics.json, table_cs2023_per_ka.csv, table_cs2023_sensitivity.csv,
         cs2023_topic_matches.csv

Metrics (seed 42, 1000x bootstrap over topics; all-MiniLM-L6-v2):
  - per-KA semantic coverage: share of that KA's CS2023 topics with
    max_cos(topic, academic_top500) >= tau; tau in {0.4,0.5,0.6,0.7}.
  - per-KA lexical coverage: share of topics exactly present in top-500.
  - reverse coverage: share of academic top-500 skills with max_cos to any
    CS2023 topic >= tau (bidirectional grounding).
"""
from __future__ import annotations

import json
import os
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

SEED = 42
BOOTSTRAP_N = 1000
PROFILE_N = 500
TAUS = [0.4, 0.5, 0.6, 0.7]
TAU = 0.5
MODEL_NAME = "all-MiniLM-L6-v2"

CS2023_TOPICS = r"""AI	Overview of AI problems, Examples of successful recent AI applications
AI	Definitions of agents with examples
AI	What is intelligent behavior?
AI	Problem characteristics
AI	Nature of agents
AI	Overview of AI Applications, growth, and impact
AI	Practice identifying problem characteristics in example environments
AI	Additional depth on nature of agents with examples
AI	Additional depth on AI Applications, Growth, and Impact
AI	Philosophical issues
AI	History of AI
AI	the Turing test and the Chinese Room thought experiment
AI	between optimal reasoning/behavior and human-like reasoning/behavior
AI	the terms: AI, machine learning, and deep learning
AI	Enumerate the characteristics of a specific problem
AI	State space representation of a problem
AI	Uninformed graph search for problem solving
AI	Heuristic graph search for problem solving
AI	Space and time complexities of graph search algorithms
AI	Bidirectional search
AI	Beam search
AI	Two-player adversarial games
AI	Implementation of A* search
AI	Constraint satisfaction
AI	Understanding the search space
AI	Local search
AI	Tabu search
AI	Variations on A*
AI	Implementation of minimax search, beam search
AI	Expectimax search and chance nodes
AI	Stochastic search
AI	the state space representation for a puzzle
AI	and implement an appropriate uninformed search algorithm for a problem
AI	and implement an appropriate informed search algorithm for a problem after designing a
AI	whether a heuristic for a given problem is admissible/can guarantee an optimal solution
AI	minimax search in a two-player adversarial game, using heuristic
AI	and implement a genetic algorithm solution to a problem
AI	and implement a simulated annealing schedule to avoid local minima in a problem
AI	and implement A*/beam search to solve a problem, and compare it against other search
AI	minimax search with alpha-beta pruning to prune search space in a two-player adversarial
AI	and contrast genetic algorithms with classic search techniques, explaining when it is most
AI	and contrast various heuristic searches vis-a-vis applicability to a given problem
AI	Types of representations
AI	Review of probabilistic reasoning, Bayes theorem
AI	Bayesian reasoning
AI	Random variables and probability distributions
AI	Independence
AI	Conditional Independence
AI	Markov chains and Markov models
AI	Utility and decision making
AI	how we can make decisions under uncertainty, using concepts such as Bayes theorem and
AI	a probabilistic inference in a real-world problem using Bayes theorem to determine the
AI	Bayes rule to determine the probability of a hypothesis given evidence
AI	the probability of outcomes and test whether outcomes are independent
AI	Definition and examples of a broad variety of machine learning tasks
AI	Fundamental ideas:
AI	A simple statistical-based supervised learning such as linear regression or decision trees
AI	The overfitting problem/controlling solution complexity
AI	Working with Data
AI	Representations
AI	Machine learning evaluation
AI	Basic neural networks
AI	Ethics for Machine Learning
AI	Ensembles of models
AI	Deep learning
AI	Performance evaluation
AI	Overview of reinforcement learning methods
AI	Two or more applications of machine learning algorithms
AI	General statistical-based learning, parameter estimation
AI	Supervised learning
AI	Overfitting
AI	Experimental design
AI	Bayesian learning
AI	Unsupervised learning and clustering
AI	Graph analysis
AI	Semi-supervised learning
AI	Graphical models
AI	Ensembles
AI	Learning theory
AI	Reinforcement learning
AI	Explainable / interpretable machine learning
AI	Recommender systems
AI	Hardware for machine learning
AI	Application of machine learning algorithms to:
AI	the differences among the three main styles of learning (supervised, reinforcement, and
AI	the terms of AI, machine learning, and deep learning
AI	overfitting in the context of a problem and learning curves and describe solutions to
AI	how machine learning works as an optimization/search process
AI	a statistical learning algorithm and the corresponding optimization process to train the
AI	the neural network training process and resulting learned representations
AI	proper ML evaluation procedures, including the differences between training and testing
AI	two machine learning algorithms on a dataset, implementing the data preprocessing and
AI	and contrast several learning techniques (e.g., decision trees, logistic regression, naive
AI	the performance of a simple learning system on a real-world dataset
AI	the problem of overfitting, along with techniques for detecting and managing the problem
AI	At least one application of AI to a specific problem and field, such as medicine, health
AI	Deployed deep generative models
AI	Overview of societal impact of AI
AI	Additional depth on deployed deep generative models
AI	Analysis and discussion of the societal impact of AI
AI	the societal impact of one or more specific real-world AI applications, identifying issues
AI	some of the failure modes of current deep generative models for language or images, and
AI	Review of propositional and predicate logic
AI	Resolution and theorem proving
AI	Knowledge representation issues
AI	Semantic web
AI	Non-monotonic reasoning
AI	Argumentation
AI	Reasoning about action and change
AI	Temporal and spatial reasoning
AI	Logic programming
AI	Rule-based Expert Systems
AI	Semantic networks
AI	Model-based and Case-based reasoning
AI	a natural language sentence into a predicate logic statement
AI	Convert a logic statement into clausal form
AI	resolution to a set of logic statements to answer a query
AI	and contrast the most common models used for structured knowledge representation
AI	the components of non-monotonic reasoning and its usefulness as a representational
AI	and contrast the basic techniques for representing uncertainty
AI	and contrast the basic techniques for qualitative representation
AI	situation and event calculus to problems of action and change
AI	the distinction between temporal and spatial reasoning, and how they interrelate
AI	the difference between rule-based, case-based, and model-based reasoning techniques
AI	the concept of a planning system and how it differs from classical search techniques
AI	the differences between planning as search, operator-based planning, and propositional
AI	the distinction between monotonic and non-monotonic inference
AI	Conditional Independence review
AI	Knowledge representations
AI	Decision Theory
AI	the probability of a hypothesis given the evidence in a Bayesian network
AI	how conditional independence assertions allow for greater efficiency of probabilistic
AI	examples of knowledge representations for reasoning under uncertainty
AI	State the complexity of exact inference. Identify methods for approximate inference
AI	and implement at least one knowledge representation for reasoning under uncertainty
AI	the complexities of temporal probabilistic reasoning
AI	and implement an HMM as one example of a temporal probabilistic system
AI	the relationship between preferences and utility functions
AI	how utility functions and probabilistic reasoning can be combined to make rational
AI	Review of propositional and first-order logic
AI	Planning operators and state representations
AI	Total order planning
AI	Partial-order planning
AI	Plan graphs and GraphPlan
AI	Hierarchical planning
AI	Planning languages and representations
AI	Multi-agent planning
AI	MDP-based planning
AI	Interconnecting planning, execution, and dynamic replanning
AI	the state representation, goal, and operators for a given planning problem
AI	Encode a planning problem in PDDL and use a planner to solve it
AI	the complete planning graph for GraphPlan to solve a given problem
AI	Agent architectures
AI	Agent theory
AI	Rationality, Game Theory
AI	Software agents, personal assistants, and information access
AI	Learning agents
AI	Cognitive systems
AI	Multi-agent systems
AI	Human-agent interaction
AI	Characterize and contrast the standard agent architectures
AI	the applications of agent theory to domains such as software agents, personal assistants
AI	the primary paradigms used by learning agents
AI	using appropriate examples how multi-agent systems support agent interaction
AI	an intelligent agent using a well-established cognitive architecture for
AI	Deterministic and stochastic grammars
AI	Parsing algorithms
AI	Representing meaning/Semantics
AI	Corpus-based methods
AI	N-grams and HMMs
AI	Smoothing and backoff
AI	Examples of use: POS tagging and morphology
AI	Information retrieval
AI	Information extraction
AI	Language translation
AI	Text classification, categorization
AI	Deep learning for NLP
AI	and contrast deterministic and stochastic grammars, providing examples to show the
AI	the challenges of representing meaning
AI	techniques for information retrieval, language translation, and text classification
AI	a TF/IDF transform, use it to extract features from a corpus, and train an off-the-shelf
AI	Overview: problems and progress
AI	Sensors and effectors
AI	Coordinate frames, translation, and rotation
AI	Configuration space and environmental maps
AI	Interpreting uncertain sensor data
AI	Localization and mapping
AI	Navigation and control
AI	Forward and inverse kinematics
AI	Motion path planning and trajectory optimization
AI	Manipulation and grasping
AI	Joint control and dynamics
AI	Vision-based control
AI	Multiple-robot coordination and collaboration
AI	Human-robot interaction
AI	Applications and Societal, Economic, and Ethical Issues
AI	fundamental motion planning algorithms within a robot configuration space
AI	and contrast at least three strategies for robot navigation within known and/or unknown
AI	at least one approach for coordinating the actions and sensing of several robots to
AI	and contrast a multi-robot coordination and a human-robot collaboration approach and
AI	the societal, economic, and ethical issues of a real-world robotics application
AI	Computer vision
AI	Audio and speech recognition
AI	Touch and proprioception
AI	Other modalities
AI	Modularity in recognition
AI	Approaches to pattern recognition
AI	the importance of image and object recognition in AI and indicate several significant
AI	at least three image-segmentation approaches, such as thresholding, edge-based and region
AI	2d object recognition based on contour-based and/or region-based shape
AI	a feature-extraction algorithm on real data, e.g., an edge or corner detector for images
AI	an algorithm combining features into higher-level percepts, e.g., a contour or polygon
AI	a classification algorithm that segments input percepts into output categories and
AI	the performance of the underlying feature-extraction, relative to at least one alternative
AI	and evaluate a deep learning solution to problems in computer vision, such as object or
AL	Abstract Data Type and operations on an ADT
AL	Arrays
AL	Records/Structs/Tuples and Objects
AL	Linked lists
AL	Stacks
AL	Queues and deques
AL	Hash tables/maps
AL	Graphs
AL	Trees
AL	Sets
AL	Search algorithms
AL	Sorting algorithms
AL	Graph algorithms
AL	Matching
AL	Cryptography algorithms
AL	Parallel algorithms
AL	Consensus algorithms
AL	Quantum computing algorithms
AL	Fast-Fourier Transform algorithm
AL	Differential evolution algorithm
AL	For each ADT/Data-Structure in this unit
AL	For each algorithm in this unit explain step-by-step how the algorithm operates
AL	For each algorithmic approach in this unit apply a prototypical example of the
AL	how collision avoidance and collision resolution is handled in hash tables
AL	factors beyond computational efficiency that influence the choice of algorithms, such as
AL	the heap property and the use of heaps as an implementation of a priority queue
AL	For each of the algorithms and algorithmic approaches in the KA Core topics:
AL	An appreciation of quantum computation and its application to certain problems
AL	Paradigms
AL	Handling exponential growth
AL	Iteration vs recursion
AL	Quantum computing
AL	For each of the paradigms in this unit
AL	Given an algorithm, explain the paradigm used by the algorithm and how it exemplifies this
AL	whether a greedy approach leads to an optimal solution
AL	various approaches for addressing computational problems whose algorithmic solutions are
AL	Complexity Analysis Framework
AL	Asymptotic complexity analysis
AL	Empirical measurements of performance
AL	Tractability and intractability
AL	Time and space tradeoffs in algorithms
AL	Little-o, Little-Omega, and Little Theta notations
AL	Formal recursive analysis
AL	Amortized analysis
AL	Turing Machine-based models of complexity
AL	Using examples, explain each of the foundational complexity classes in this unit
AL	Informally evaluate the foundational complexity class of simple algorithms
AL	empirical studies to determine and validate hypotheses about the runtime complexity of
AL	examples that illustrate time-space tradeoffs of algorithms
AL	how tree balance affects the efficiency of binary search tree operations
AL	the significance of NP-Completeness
AL	how NP-Hard is a lower bound and NP is an upper bound for NP-Completeness
AL	examples of NP-complete problems
AL	recurrence relations to evaluate the time complexity of recursively defined algorithms
AL	elementary recurrence relations using a form of the Master Theorem
AL	Big-O notation to give upper case bounds on time/space complexity of algorithms
AL	the Cook-Levin Theorem and the NP-Completeness of SAT
AL	the classes P and NP
AL	the P-space class and its relation to the EXP class
AL	Formal automata
AL	Formal languages, grammars and Chomsky Hierarchy
AL	Relations among formal automata, languages, and grammars
AL	Decidability,computability, and halting
AL	The Church-Turing thesis
AL	Algorithmic correctness
AL	Deterministic and nondeterministic automata
AL	Pumping Lemma proofs
AL	Decidability
AL	Reducibility and reductions
AL	Time complexity based on Turing Machine
AL	Space complexity
AL	Equivalent models of algorithmic computation
AL	Quantum computation
AL	For each formal automaton in this unit:
AL	Given a problem, develop an appropriate automaton that addresses the problem
AL	a regular expression for a given regular language expressed in natural language
AL	the difference between regular expressions and the regular expressions
AL	For each formal model in this unit:
AL	a universal Turing Machine and its operation
AL	examples of classic uncomputable problems
AL	the Church-Turing Thesis and its significance for algorithmic computation
AL	how invariants can be used to prove the correctness of an algorithm
AL	For each formal automaton in this unit explain its deterministic and
AL	arithmetization and diagonalization to prove the Halting Problem for Turing Machines is
AL	Rices theorem and its significance
AL	an example proof of a problem that is uncomputable by reducing a classic known
AL	the Primitive and General Recursive functions (zero, successor, selection, primitive
AL	how computation is performed in Lambda Calculus (e.g., Alpha conversion and Beta
AL	For a quantum system give examples that explain the following postulates
AL	the operation of a quantum XNOT or CNOT gate on a quantum bit represented as a matrix
AL	Social, ethical, and secure algorithms
AL	Algorithmic fairness
AL	Anonymity
AL	Accountability/Transparency
AL	Responsible algorithms
AL	Economic and other impacts of inefficient algorithms
AL	Sustainability
AL	Context aware computing
AL	algorithmic solutions to real-world societal problems, such as routing an ambulance to a
AL	the impact that an algorithm may have on the environment and society when used to solve
AL	an example that articulates how differential privacy protects knowledge of an individuals
AL	the environmental impacts of design choices that relate to algorithm design
AL	the tradeoffs involved in proof-of-work and proof-of-stake algorithms
AR	Combinational vs sequential logic/field programmable gate arrays
AR	Computer-aided design tools that process hardware and architectural representations
AR	High-level synthesis
AR	System-on-chip design flow
AR	Physical constraints
AR	the progression of computer technology components from vacuum tubes to VLSI, from
AR	parallelism and data dependencies between and within components in a modern
AR	the relationship between parallelism and power consumption
AR	the design of basic building blocks for a computer: arithmetic-logic unit
AR	simple building blocks
AR	the timing behavior of a pipelined processor, identifying data dependency issues
AR	Overview and history of computer architecture
AR	Bits, bytes, and words
AR	Unsigned, signed and twos complement representations
AR	Numeric data representation and number bases
AR	Representation of non-numeric data
AR	Representation of records, arrays and UTF data types
AR	why everything in computers are data, including instructions
AR	how fixed-length number representations can affect accuracy and precision
AR	how negative integers are stored in sign-magnitude and twos-complement
AR	how different formats can represent numerical data
AR	numerical data from one format to another
AR	how a single adder can handle both signed (twos
AR	von Neumann machine architecture
AR	Control unit: instruction fetch, decode, and execution
AR	Introduction to SIMD vs MIMD and the Flynn taxonomy
AR	Shared memory multiprocessors/multicore organization
AR	Instruction set architecture
AR	Subroutine call and return mechanisms
AR	I/O and interrupts
AR	Heap, static, stack, and code segments
AR	how the classical von Neumann functional units are implemented in embedded systems
AR	how instructions are executed in a classical von Neumann machine, with extensions for
AR	how instructions are represented at the machine level and in the context of a symbolic
AR	Map an example of high-level language patterns into assembly/machine language notations
AR	a subroutine diagram to comment on how subroutine calls are handled at the assembly
AR	basic concepts of interrupts and I/O operations
AR	a simple assembly language program for string/array processing and manipulation
AR	Memory hierarchy: the importance of temporal and spatial locality
AR	Main memory organization and operations
AR	Persistent memory
AR	Latency, cycle time, bandwidth, and interleaving
AR	Cache memories
AR	Multiprocessor cache coherence
AR	Virtual memory
AR	Fault handling and reliability
AR	Reliability
AR	Processing In-Memory
AR	Using a memory system diagram, identify the main types of memory technology (e.g., SRAM
AR	the effect of memory latency on running time
AR	Enumerate the functions of a system with virtual memory management
AR	average memory access time under various cache and memory configurations and mixes
AR	I/O fundamentals
AR	Interrupt structures: vectored and prioritized, interrupt acknowledgment
AR	I/O devices
AR	External storage, physical organization, and drives
AR	Buses fundamentals
AR	an interrupt control diagram to comment on how interrupts are used to implement I/O
AR	Enumerate various types of buses in a computer system
AR	the advantages of magnetic disks and contrast them with those of solid-state disks
AR	Control unit
AR	Instruction pipelining
AR	Introduction to instruction-level parallelism
AR	alternative implementation of datapaths in modern computer architectures
AR	instruction-level parallelism using pipelining and significant hazards that may occur
AR	a complete processor, including datapath and control
AR	the average cycles per instruction for a given processor and memory system
AR	Performance-energy evaluation: performance, power consumption, memory, and
AR	Branch prediction, speculative execution, out-of-order execution, Tomasulo's algorithm
AR	Enhancements for vector processors and GPUs
AR	Hardware support for multithreading
AR	Scalability
AR	Dynamic voltage and frequency scaling
AR	Dark Silicon
AR	performance and energy efficiency evaluation metrics
AR	a speculative execution diagram and write about the decisions that can be made
AR	a GPU performance-watt benchmarking diagram
AR	a multithreaded program that adds elements of two integer vectors
AR	Recommend a set of design choices for alternative computer architectures
AR	Enumerate key concepts associated with dynamic voltage and frequency scaling
AR	energy savings improvement for an 8-bit integer quantization compared to a 32-bit
AR	SIMD and MIMD architectures
AR	Heterogeneous memory systems
AR	Domain-Specific Architectures
AR	Packaging and integration solutions such as 3DIC and chiplets
AR	Machine learning in architecture design
AR	what memory-management issues are found in multiprocessors that are not present in
AR	how you would determine when to use a domain-specific accelerator instead of a general
AR	the advantages and disadvantages of a PIM architecture
AR	Principles of Secure Hardware
AR	Roots of trust in hardware, Physically Unclonable Functions
AR	Hardware Random Number Generators
AR	Memory protection extensions
AR	Trusted Execution Environment
AR	Homomorphic encryption for privacy-preserving data processing
AR	how Physically Unclonable Functions can be a unique device identifier in security
AR	the advantages and disadvantages of memory protection at the ISA level
AR	key design issues of a trusted execution environment to support virtual machines
AR	Principles
AR	Axioms of QM: superposition principle, measurement axiom, unitary evolution
AR	Single qubit gates for the circuit model of quantum computation: X, Z, H
AR	Two qubit gates and tensor products, working with matrices
AR	The No-Cloning Theorem. The Quantum Teleportation protocol
AR	Algorithms
AR	Implementation aspects
AR	Emerging Applications
AR	how a quantum object produced as a particle propagates like a wave and is detected as a
AR	the quantum-level nature that is inherently probabilistic
AR	quantum parallelism and the role of constructive vs destructive interference in quantum
AR	a code snippet providing the role of quantum Fourier transform in Shors algorithm
AR	Environmental impacts of implementation decisions
DM	the five stages of the Data Life Cycle
DM	Purpose and advantages of database systems
DM	Components of database systems
DM	of core DBMS functions (e.g., query mechanisms, transaction management, buffer
DM	Database architecture, data independence, and data abstraction
DM	Transaction management
DM	Normalization
DM	Approaches for managing large volumes of data (e.g., NoSQL database systems, use of
DM	How to support CRUD-only applications
DM	Distributed databases/cloud-based systems
DM	Structured, semi-structured, and unstructured data
DM	of a declarative query language
DM	Systems supporting structured and/or stream content
DM	at least four advantages that using a database system provides
DM	Enumerate the components of a database system
DM	Follow a query as it is processed by the components of a database system
DM	Defend the value of data independence
DM	Compose a simple select-project-join query in SQL
DM	Enumerate the four properties of a correct transaction manager
DM	the advantages for eliminating duplicate repeated data
DM	Outline how MapReduce uses parallelism to process data efficiently
DM	the differences between structured and semi/unstructured databases
DM	Data modeling
DM	Relational data model
DM	Conceptual models
DM	Semi-structured data models
DM	Spreadsheet models
DM	Object-oriented models
DM	New features in SQL
DM	Specialized Data Modeling topics
DM	the components of the relational data model
DM	1:1, 1:n, and n:m relationships using the relational data model
DM	the components of the E-R data model
DM	a given environment using a conceptual data model
DM	a given environment using the document-based or key-value store-based data model
DM	Entity and referential integrity: Candidate key, superkeys
DM	Relational database design
DM	Mapping conceptual schema to a relational schema
DM	Physical database design: file and storage structures
DM	Introduction to Functional dependency theory
DM	Normalization Theory
DM	Functional dependency theory
DM	the defining characteristics behind the relational data model
DM	Comment on the difference between a foreign key and a superkey
DM	Enumerate the different types of integrity constraints
DM	Compose a relational schema from a conceptual schema which contains 1:1, 1:n, and n:m
DM	Map appropriate file structure to relations and indices
DM	how functional dependency theory generalizes the notion of key
DM	Defend a given decomposition as lossless and or dependency preserving
DM	Detect which normal form a given decomposition yields
DM	Comment on reasons for denormalizing a relation
DM	SQL Query Formation
DM	Relational Algebra
DM	SQL
DM	Relational Calculus
DM	QBE and 4th-generation environments
DM	Different ways to invoke non-procedural queries in conventional languages
DM	Introduction to other major query languages
DM	Stored procedures
DM	when a nested SQL query is correlated or not
DM	Iterate over data retrieved programmatically from a database via an SQL query
DM	Compose an SQL query to update a tuple in a relation
DM	Page structures
DM	Index structures
DM	File structures
DM	Algorithms for query operators
DM	Query transformations
DM	Query optimization
DM	Parallel Query Processing
DM	Database tuning/performance
DM	the purpose and organization of both B+ tree and hash index structures
DM	Compose an SQL command to create an index
DM	the steps for the various query operator algorithms: external sorting, projection with
DM	Derive the run-time for each of the above algorithms
DM	selectivity estimates for a given selection and/or join operation
DM	how DBMSs leverage parallelism to speed up query processing by dividing the work
DM	DB Buffer Management
DM	Transaction Management
DM	Concurrency Control:
DM	Recovery Manager
DM	how a DBMS manages its Buffer Pool
DM	the four properties for a correct transaction manager
DM	Outline the principle of serializability
DM	Why NoSQL?
DM	Key-Value and Document data model
DM	Storage systems
DM	Distribution Models
DM	Graph Databases
DM	Consistency Models
DM	Processing model
DM	Case Studies: Cloud storage system; Graph databases; When not to use NoSQL (See
DM	a use case for the use of NoSQL over RDBMS
DM	the defining characteristics behind Key-Value and Document-based data models
DM	Differences between data security and data privacy
DM	Protecting data and database systems from attacks, including injection attacks such as SQL
DM	Personally identifying information and its protection
DM	Ethical considerations in ensuring the security and privacy of data
DM	Database auditing and its role in digital forensics
DM	Data inferencing and preventing attacks
DM	Laws and regulations governing data security and data privacy
DM	Typical risk factors and prevention measures for ensuring data integrity
DM	Ransomware and prevention of data loss and destruction
DM	the differences in the goals for data security and data privacy
DM	and mitigate risks associated with different approaches to protecting data
DM	legal and ethical considerations of end-to-end data security and privacy
DM	a database auditing system given risk considerations
DM	several data exploration approaches to understanding unfamiliar datasets
DM	Exploratory data techniques
DM	Data acquisition and governance
DM	Data security and privacy considerations
DM	Data fairness and bias
DM	Data visualization techniques and their use in data analytics
DM	Entity Resolution
DM	several data exploration approaches, including visualization, to understanding unfamiliar
DM	several data exploration approaches to understanding unfamiliar datasets
DM	basic machine learning/data mining algorithms and when they are appropriate for use
DM	several machine learning/data mining algorithms
DM	legal and ethical considerations in acquiring, using, and modifying datasets
DM	issues of fairness and bias in data collection and usage
DM	Distributed DBMS
DM	Parallel DBMS
DM	Vectorized unstructured data and vector storage
DM	Semi-structured databases
DM	Issues related to scale
DM	Data privacy overall
DM	Data anonymity
DM	Data ownership/custodianship
DM	Intended and unintended applications of stored data
DM	Reliability of data
DM	Provenance, data lineage, and metadata management
DM	Data security
DM	Enumerate three social and three legal issues related to large data collections
DM	the value of data privacy
DM	the competing stakeholders with respect to data ownership
DM	Enumerate three negative unintended consequences from a given data-centric
DM	the meaning of data provenance and lineage
DM	how a database might contribute to data security as well as how it may introduce
FPL	Imperative programming as a subset of object-oriented programming
FPL	Object-oriented design:
FPL	Definition of classes: fields, methods, and constructors
FPL	Subclasses, inheritance, and method overriding
FPL	Dynamic dispatch: definition of method-call
FPL	Exception handling
FPL	Object-oriented idioms for encapsulation:
FPL	Dynamic vs static properties
FPL	Composition vs inheritance
FPL	Subtyping:
FPL	Collection classes, iterators, and other common library components
FPL	Metaprogramming and reflection
FPL	Enumerate the differences between imperative and object-oriented programming paradigms
FPL	a simple class hierarchy utilizing subclassing that allows code to be reused for distinct
FPL	and validate control flow in a program using dynamic dispatch
FPL	and contrast how computational solutions to a problem differ in procedural, functional
FPL	and contrast mechanisms to define and protect data elements within procedural
FPL	and contrast the benefits and costs/impact of using inheritance and
FPL	the relationship between object-oriented inheritance and
FPL	object-oriented encapsulation mechanisms such as interfaces and private members
FPL	and use iterators and other operations on aggregates, including operations that take
FPL	collection classes and iterators effectively to solve a problem
FPL	Lambda expressions and evaluation:
FPL	Effect-free programming:
FPL	Processing structured data via functions with cases for each data variant:
FPL	Using higher-order functions
FPL	Metaprogramming and reflection
FPL	Function closures
FPL	Graph reduction machine and call-by-need
FPL	Implementing lazy evaluation
FPL	Integration with other programming paradigms such as imperative and object-oriented
FPL	basic algorithms that avoid assigning to mutable states or considering reference equality
FPL	useful functions that take and return other functions
FPL	and contrast how computational solutions to a problem differ in procedural, functional
FPL	and contrast mechanisms to define and protect data elements within procedural
FPL	a simple example of lambda expression being implemented using a virtual machine, such
FPL	Correctly interpret variables and lexical scope in a program using function closures
FPL	functional encapsulation mechanisms such as closures and modular interfaces
FPL	and contrast stateful vs stateless execution
FPL	and use iterators and other operations on aggregates, including operations that take
FPL	Illustrate graph reduction using a -expression using a shared subexpression
FPL	Universal vs existential quantifiers
FPL	First order predicate logic vs higher order logic
FPL	Expressing complex relations using logical connectives and simpler relations
FPL	Definitions of Horn clause, facts, goals and subgoals
FPL	Unification and unification algorithm; unification vs assertion vs expression evaluation
FPL	Mixing relations with functions
FPL	Cuts, backtracking, and non-determinism
FPL	Closed-world vs open-world assumptions
FPL	Memory overhead of variable copying in handling iterative programs
FPL	Programming constructs to store partial computation and pruning search trees
FPL	Higher-order, constraint, and inductive logic programming
FPL	Integration with other programming paradigms such as object-oriented programming
FPL	a logic language to implement a conventional algorithm
FPL	a simple illustrative example to show correspondence between First Order Predicate Logic
FPL	simple logic programs interleaving relations, functions, and recursive programming such as
FPL	Error/exception handling
FPL	Piping
FPL	System commands
FPL	Environment variables
FPL	File abstraction and operators
FPL	Data structures, such as arrays and lists
FPL	Regular expressions
FPL	Programs and processes
FPL	Workflow
FPL	and execute automated scripts to manage various system tasks
FPL	Solve various text processing problems through scripting
FPL	Procedural programming vs reactive programming: advantages of reactive programming in
FPL	Stateless and state-transition models of event-based programming
FPL	Canonical uses such as GUIs, mobile devices, robots, servers
FPL	Using a reactive framework:
FPL	Separation of model, view, and controller
FPL	Event-driven and reactive programs as state-transition systems
FPL	event handlers for use in reactive systems, such as GUIs
FPL	and use a reactive framework
FPL	an interactive system in terms of a model, a view, and a controller
FPL	Safety and liveness
FPL	Programming models
FPL	Properties
FPL	Execution control:
FPL	Communication and coordination
FPL	Futures
FPL	Language support for data parallelism such as forall, loop unrolling, map/reduce
FPL	Effect of memory-consistency models on language semantics and correct code generation
FPL	Representational State Transfer Application Programming Interfaces
FPL	Overheads of message-passing
FPL	Granularity of program for efficient exploitation of concurrency
FPL	Concurrency and other programming paradigms
FPL	why programming languages do not guarantee sequential consistency in the presence of
FPL	correct concurrent programs using multiple programming models, such as shared
FPL	a message-passing model to analyze a communication protocol
FPL	synchronization constructions such as monitor/synchronized methods in a simple program
FPL	Modeling data dependency using simple programming constructs involving variables, read and
FPL	Modeling control dependency using simple constructs such as selection and iteration
FPL	how REST API's integrate applications and automate processes
FPL	benefits, constraints and challenges related to distributed and parallel computing
FPL	Aspects
FPL	Join points
FPL	Advice
FPL	Point cuts
FPL	Weaving  static and dynamic
FPL	Alternatives including annotations and IDEs
FPL	A type as a set of values together with a set of operations
FPL	Association of types to variables, arguments, results, and fields
FPL	Type safety as an aspect of program correctness
FPL	Type safety and errors caused by using values inconsistently given their intended types
FPL	Generic types
FPL	Type equivalence: structural vs name equivalence
FPL	Complementary benefits of static and dynamic typing:
FPL	Compositional type constructors, such as product types, sum types
FPL	Type checking
FPL	Subtyping:
FPL	Type safety as preservation plus progress
FPL	Type inference
FPL	Static overloading
FPL	Propositions as types
FPL	Describe, for both a primitive and a compound type, the values that have that type
FPL	examples of program errors detected by a type system
FPL	program properties, for multiple programming languages, that are checked statically and
FPL	an example program that does not type-check in a particular language and yet would have
FPL	types and type-error messages to write and debug programs
FPL	how typing rules define the set of operations that are legal for a type
FPL	the type rules governing the use of a particular compound type
FPL	why undecidability requires type systems to conservatively approximate program behavior
FPL	and use program pieces that use generic types
FPL	the differences among generics, subtyping, and overloading
FPL	multiple benefits and limitations of static typing in writing, maintaining, and debugging
FPL	a type system precisely and compositionally
FPL	Precisely describe the invariants preserved by a sound type system
FPL	Prove type safety for a simple language in terms of preservation and progress theorems
FPL	a unification-based type-inference algorithm for a simple language
FPL	how static overloading and associated resolution algorithms influence the dynamic behavior
FPL	Direct, indirect, and indexed access to memory location
FPL	Run-time layout of memory: activation record, static data, call-stack, heap
FPL	Memory management:
FPL	Green computing
FPL	how a core language construct, such as data abstractions and control abstractions, is
FPL	how programming language implementations typically organize memory into global data
FPL	why memory leaks and dangling pointer problems occur, and what can be done by a
FPL	Execution models for JIT, compiler, interpreter
FPL	of intermediate code, e.g., bytecode
FPL	Limitations and benefits of JIT, compiler, and interpreter
FPL	Cross compilers/transpilers
FPL	BNF and extended BNF representation of context-free grammar
FPL	Parse tree using a simple sentence such as arithmetic expression or if-then-else statement
FPL	Execution as native code or within a virtual machine
FPL	Run-time representation of core language constructs such as objects and first-class
FPL	Secure compiler development
FPL	and understand the differences between compiled, JIT, and interpreted language
FPL	syntax and parsing from semantics and evaluation
FPL	BNF and extended BNF to specify the syntax of simple constructs such as if-then-else, type
FPL	Illustrate the parse tree using a simple sentence/arithmetic expression
FPL	the benefits and limitations of garbage collection, including the notion of reachability
FPL	BNF and regular expressions
FPL	Programs that take programs as input such as interpreters, compilers, type-checkers
FPL	Components of a language:
FPL	Program as a set of non-ambiguous meaningful sentences
FPL	Basic programming abstractions: constants, variables, declarations
FPL	Mutable vs immutable variables: advantages and disadvantages of reusing existing memory
FPL	Scope rules: static vs dynamic; visibility of variables; side-effects
FPL	Side-effects induced by nonlocal variables, global variables and aliased variables
FPL	Environment vs store and their properties
FPL	Data and control abstraction
FPL	Data structures to represent code for execution, translation, or transmission
FPL	Lambda calculus, variable binding, and variable renaming
FPL	Illustrate the scope of variables and visibility using simple programs
FPL	Illustrate different types of parameter-passing using simple pseudo programming language
FPL	side-effect using global and nonlocal variables and how to fix such programs
FPL	how programs that process other programs treat the other programs as their input data
FPL	a grammar and an abstract syntax tree for a small language
FPL	the benefits of having program representations other than strings of source code
FPL	a program to process some representation of code for some purpose, such as an
FPL	Regular grammars vs context-free grammars
FPL	Scanning and parsing based on language specifications
FPL	Lexical analysis using regular expressions
FPL	Tokens and their use
FPL	Parsing strategies including top-down and bottom-up (e.g., LR or
FPL	Language theory:
FPL	Parser error recovery mechanisms
FPL	Generating scanners and parsers from declarative specifications
FPL	formal grammars to specify the syntax of languages
FPL	Illustrate the role of lookahead tables in parsing
FPL	declarative tools to generate parsers and scanners
FPL	key issues in syntax definitions: ambiguity, associativity, precedence
FPL	Abstract syntax trees; contrast with concrete syntax
FPL	Defining, traversing, and modifying high-level program representations
FPL	Scope and binding resolution
FPL	Static semantics
FPL	L-values/R-values
FPL	Call semantics
FPL	Draw the abstract syntax tree for a small language
FPL	context-sensitive, source-level static analyses such as type-checkers or resolving
FPL	semantic analyses using an attribute grammar
FPL	Undecidability and consequences for program analysis
FPL	Flow-insensitive analysis, such as type-checking and scalable pointer and alias analysis
FPL	Flow-sensitive analysis, such as forward and backward dataflow analyses
FPL	Path-sensitive analysis, such as software model checking and software verification
FPL	Tools and frameworks for implementing analyzers
FPL	Role of program analysis in verification and bug-finding
FPL	Parallelization:
FPL	the difference between dataflow graph and control flow graph
FPL	why non-trivial sound program analyses must be approximate
FPL	Argue why an analysis is correct
FPL	why potential aliasing limits sound program analysis and how alias analysis can help
FPL	Instruction sets
FPL	Control flow
FPL	Memory management
FPL	Procedure calls and method dispatching
FPL	Separate compilation; linking
FPL	Instruction selection
FPL	Instruction scheduling
FPL	Register allocation
FPL	Code optimization as a form of program analysis
FPL	Program generation through generative AI
FPL	the low-level code necessary for calling functions/methods in modern languages
FPL	why separate compilation requires uniform calling conventions
FPL	why separate compilation limits optimization because of unknown effects of calls
FPL	Process models using stacks and heaps to allocate and deallocate activation records and
FPL	Data layout for objects and activation records
FPL	Object allocation in heap
FPL	Run-time behavior of object-oriented programs
FPL	and contrast allocation of memory during information exchange using parameter-passing
FPL	Dynamic memory management approaches and techniques: malloc/free, garbage collection (mark
FPL	Just-in-time compilation and dynamic recompilation
FPL	Interface to operating system
FPL	Interoperability between programming languages including parameter-passing mechanisms and
FPL	Sandboxing
FPL	benefits and limitations of automatic memory management
FPL	the use of metadata in run-time representations of objects and activation records, such as
FPL	and contrast static allocation vs stack-based allocation vs heap-based allocation of data
FPL	why some data elements cannot be automatically deallocated at the end of a
FPL	advantages, disadvantages, and difficulties of just-in-time and dynamic recompilation
FPL	the use of sandboxing in mobile code
FPL	the services provided by modern language run-time systems
FPL	Encapsulation mechanisms
FPL	Lazy evaluation and infinite streams
FPL	and contrast lazy evaluation vs eager evaluation
FPL	Unification vs assertion vs expression evaluation
FPL	Control abstractions: exception handling, continuations, monads
FPL	Object-oriented abstractions: multiple inheritance, mixins, traits, multimethods
FPL	Metaprogramming: macros, generative programming, model-based development
FPL	String manipulation via pattern-matching
FPL	Dynamic code evaluation
FPL	Language support for checking assertions, invariants, and pre/post-conditions
FPL	Domain specific languages, such as database languages, data science languages, embedded
FPL	Massive parallel high performance computing models and languages
FPL	various advanced programming constructs and idioms correctly
FPL	how various advanced programming constructs aim to improve program structure, software
FPL	how various advanced programming constructs interact with the definition and
FPL	Problem domains and programming paradigm
FPL	Criteria for good programming language design
FPL	Evaluation order, precedence, and associativity
FPL	Eager vs delayed evaluation
FPL	Defining control and iteration constructs
FPL	External calls and system libraries
FPL	the role of concepts such as orthogonality and well-chosen defaults in language design
FPL	Objectively evaluate and justify language-design decisions
FPL	an example program whose result can differ under different rules for evaluation order
FPL	Illustrate uses of delayed evaluation, such as user-defined control abstractions
FPL	Syntax vs semantics
FPL	Approaches to semantics: axiomatic, operational, denotational, type-based
FPL	Operational semantics analysis of abstract constructs and sequence of such as assignment
FPL	Denotational semantics
FPL	Proofs by induction over language semantics
FPL	Formal definitions and proofs for type systems
FPL	formal semantics for a small language
FPL	a lambda-calculus program and show its evaluation to a normal form
FPL	the different approaches of operational, denotational, and axiomatic semantics
FPL	induction to prove properties of all programs in a language
FPL	parametricity to establish the behavior of code given only its type
FPL	Formal specification languages and methodologies
FPL	Theorem provers, proof assistants, and logics
FPL	Constraint checkers
FPL	Formal modeling and manual refinement/implementation of software systems
FPL	of symbolic testing and fuzzing in software development
FPL	checking
FPL	formal modeling techniques to develop and validate architectures
FPL	verifier and specification support in programming languages to formally validate system
FPL	Integrate symbolic validation tooling into a programming workflow
FPL	when and how formal methods can be effectively used in the development process
FPL	Language design principles
FPL	Designing a language to fit a specific domain or problem
FPL	Interoperability between programming languages
FPL	Language portability
FPL	Formal description of a programming language
FPL	Green computing principles
FPL	Impact of English-centric programming languages
FPL	Enhancing accessibility and inclusivity for people with disabilities  Supporting assistive
FPL	Human factors related to programming languages and usability
FPL	Etymology of terms such as class, master, and slave in programming languages
FPL	Increasing accessibility by supporting multiple languages within applications
FPL	Consciously design programming languages to be inclusive and non-offensive
FPL	Professional: Students must demonstrate and apply the highest standards when using
FPL	Meticulous: Attention to detail is essential when using programming languages and applying
FPL	Proactive: Programmers are responsible for anticipating all forms of user input and system
GIT	Uses of computer graphics and interactive techniques and their potential risks and abuses
GIT	Graphic output
GIT	Human vision system
GIT	Standard image formats
GIT	Digitization of analog data
GIT	Color models: additive, subtractive, and color perception
GIT	Tradeoffs between storing image data and re-computing image data
GIT	Spatialization: coordinate systems, absolute and relative positioning
GIT	Animation as a sequence of still images
GIT	Applied interactive graphics
GIT	Display characteristics
GIT	common uses of digital presentation to humans
GIT	how analog signals can be reasonably represented by discrete samples, for example, how
GIT	the memory requirement for storing a color image given its resolution
GIT	a graphic depicting how the limits of human perception affect choices about the digital
GIT	color models and their use in graphics display devices
GIT	the memory requirements for a multi-second movie displaying at a
GIT	and contrast digital video to analog video
GIT	the basic process of producing continuous motion from a sequence of discrete frames
GIT	a possible visual misrepresentation that could result from digitally sampling an analog
GIT	memory space requirements based on resolution and color coding
GIT	time requirements based on refresh rates and rasterization techniques
GIT	a user interface and an alternative for persons with color perception deficiency
GIT	a simple graphical user interface using a graphics library
GIT	Scientific Data Visualization and Information Visualization
GIT	Visualization techniques
GIT	Visualization pipeline
GIT	High-dimensional data handling techniques
GIT	Perceptual and cognitive foundations that drive visual abstractions
GIT	and evaluation of visualizations
GIT	and contrast data visualization and information visualization
GIT	Deploy basic algorithms for visualization
GIT	the tradeoffs of visualization algorithms in terms of accuracy and performance
GIT	the effectiveness of a given visualization for a particular task
GIT	a process to evaluate the utility of a visualization algorithm or system
GIT	Object and scene modeling
GIT	Camera and projection modeling
GIT	Radiometry and light models
GIT	Rendering
GIT	the basic rendering pipeline
GIT	and contrast how forward and backwards rendering factor into the graphics pipeline
GIT	a program to display 2D shapes in a window
GIT	a program to display 3D models
GIT	Produce linear perspective from similar triangles by converting points to points
GIT	two-dimensional and 3-dimensional points by applying affine transformations
GIT	texture mapping, sampling, and anti-aliasing, and describe examples of each
GIT	ray tracing and rasterization for the visibility problem
GIT	a program that performs transformation and clipping operations on simple two
GIT	a simple real-time renderer using a rasterization API using
GIT	and contrast the different rendering techniques
GIT	and contrast the difference in transforming the camera vs the models
GIT	Surface representation/model
GIT	Volumetric representation/model
GIT	Procedural representation/model
GIT	Multi-resolution modeling
GIT	Reconstruction, e.g., 3D scanning, photogrammetry
GIT	Contrast representing curves and surfaces in both implicit and parametric forms
GIT	simple polyhedral models by surface tessellation
GIT	a mesh representation from an implicit surface
GIT	a fractal model or terrain using a procedural method
GIT	a mesh from data points acquired with a laser scanner
GIT	CSG models from simple primitives, such as cubes and quadric surfaces
GIT	Solutions and approximations to the rendering equation, for example
GIT	Time, lens position, and continuous frequency and their impact on
GIT	Shadow mapping
GIT	Occlusion culling
GIT	Bidirectional Scattering Distribution function theory and microfacets
GIT	Subsurface scattering
GIT	Area light sources
GIT	Hierarchical depth buffering
GIT	Image-based rendering
GIT	Non-photorealistic rendering
GIT	Realtime rendering
GIT	GPU architecture
GIT	how an algorithm estimates a solution to the rendering equation
GIT	the properties of a rendering algorithm
GIT	the bandwidth and computation demands of a simple shading algorithm
GIT	a non-trivial shading algorithm under a
GIT	State how a particular artistic technique might be implemented in a renderer
GIT	how one might recognize the shading techniques used to create a particular image
GIT	a ray tracer for scenes using a simple Bidirectional Reflection Distribution
GIT	Types of animation
GIT	Key-frame animation
GIT	Forward and inverse kinematics
GIT	Skinning algorithms
GIT	Motion capture
GIT	the location and orientation of model parts using a forward kinematic approach
GIT	the orientation of articulated parts of a model from a location and orientation using an
GIT	the tradeoffs in different representations of rotations
GIT	Collision detection and response
GIT	Procedural animation using noise
GIT	Particle systems
GIT	Grid-based fluids
GIT	Heightfields
GIT	Rule-based systems
GIT	algorithms for physical modeling of particle dynamics using simple Newtonian
GIT	a smoke solver with user interaction
GIT	Immersion levels, Augmented Reality, and Mixed Reality)
GIT	Definitions of and distinctions between immersion and presence
GIT	360 Video
GIT	Stereoscopic display
GIT	Viewer tracking
GIT	Time-critical rendering to achieve optimal Motion To Photon latency
GIT	Distributed VR, collaboration over computer network
GIT	Presence and factors that impact level of immersion
GIT	3D interaction
GIT	Applications in medicine, simulation, training, and visualization
GIT	Safety in immersive applications
GIT	a stereoscopic image
GIT	and write an AR or VR application
GIT	the pros and cons of different types of viewer tracking
GIT	and contrast the differences between geometry- and image-based virtual reality
GIT	the design issues of user action synchronization and data consistency in a networked
GIT	the specifications for an augmented reality application to be used by surgeons in the
GIT	Assess an immersive applications accessibility
GIT	the most important technical characteristics of a VR system/application that should be
GIT	Event Driven Programming
GIT	Graphical User Interface
GIT	Accessibility
GIT	Gestural Interfaces
GIT	Haptic Interfaces
GIT	Multimodal Interfaces
GIT	Head-worn Interfaces
GIT	Natural Language Interfaces
GIT	a simple game that responds to single channel mouse and keyboard events
GIT	a mobile app that responds to touch events
GIT	and create an application that responds to different event triggers
GIT	Assess the consistency or lack of consistency in cross-platform touch screen gestures
GIT	and create an application that provides haptic feedback
GIT	a program that is controlled by gestures
GIT	Morphological operations
GIT	Color histograms
GIT	Image enhancement
GIT	Image restoration
GIT	Image coding
GIT	Connections to deep learning
GIT	a program that uses dilation and erosion to smooth the edges of a binary image
GIT	Manipulating the hue of an image
GIT	a program that applies a high-pass filter to an image. (The advanced variation would be to
GIT	Assess the results of selectively filtering an image in the frequency domain
GIT	Interaction with the physical world
GIT	Connection to physical artifacts
GIT	Internet of Things
GIT	a simple virtual switch or application button and use it to turn on an LED
GIT	a simple system to move a servo in response to sensor data
GIT	a 3D form in a CAD package
GIT	the G- and M-Code to construct a 3D maze and use a CAD/CAM package to check your
GIT	Accessibility in immersive, interactive, and physical computing applications
GIT	Ethics/privacy in graphics applications
GIT	Intellectual Property law as it relates to computer graphics and interactive techniques
GIT	Current and past contributors to the field
GIT	the security issues inherent in location tags
GIT	the copyright issues of using watermarked images to train a neural network
GIT	Coordinate geometry
GIT	Trigonometry
GIT	MSF-Linear*
GIT	MSF-Calculus*
GIT	MSF-Linear
GIT	MSF-Calculus
GIT	MSF-Probability
GIT	MSF-Statistics
GIT	MSF-Discrete
GIT	Data Structures necessary for this knowledge area
GIT	Data Structures desirable for this knowledge area
HCI	User-centered design and evaluation methods
HCI	User-centered design methodology
HCI	Physical and cognitive characteristics of the user
HCI	Designing for diverse user populations
HCI	Collaboration and communication
HCI	Multi-user systems
HCI	Conduct a user-centered design process that is integrated into a project
HCI	and contrast the needs of users with those of designers
HCI	the representative users of a design and discuss who else could be impacted by it
HCI	empathy and evaluation as elements of the design process
HCI	Carry out and document an analysis of users and their needs
HCI	a user story from a needs assessment
HCI	Contrast the different needs-finding methods for a given design problem
HCI	Reflect on whether your design would benefit from low-tech or no-tech components
HCI	the implications of designing for a multi-user system/context
HCI	impact
HCI	Ethics in design methods and solutions
HCI	Requirements in design
HCI	Value-sensitive design
HCI	Persuasion through design
HCI	and critique the potential impacts of a design on society and relevant communities to
HCI	the potential human factor elements in a design
HCI	and understand direct and indirect stakeholders
HCI	scenarios that consider the entire lifespan of a design, beyond the immediately planned
HCI	Assess the persuasive content of a design and its intent relative to user interests
HCI	Critique the outcomes of a design given its intent
HCI	Understand the impact of design decisions
HCI	Background
HCI	Techniques
HCI	Technologies
HCI	IDFs
HCI	Universal design
HCI	Inclusive Design Frameworks
HCI	Technologies: the Return On Investment of inclusion
HCI	Inclusive Design Frameworks: user-sensitive inclusive design
HCI	Critical approaches to HCI
HCI	appropriate inclusive design approaches, such as universal design and ability-based
HCI	and demonstrate understanding of software accessibility guidelines
HCI	recognition of laws and regulations applicable to accessible design
HCI	inclusive frameworks to design, such as universal design and usability and ability-based
HCI	understanding of laws and regulations applicable to accessible design
HCI	understanding of what is appropriate and inappropriate high level of skill during
HCI	web pages and mobile apps for current standards of accessibility
HCI	Conceptualize user experience research to identify user needs and generate design insights
HCI	Methods for evaluation with users
HCI	Study planning
HCI	Techniques and tools for quantitative analysis
HCI	Data management
HCI	the differences between formative and summative assessment and their role in evaluating
HCI	appropriate formative or summative evaluation methods at different points throughout the
HCI	the benefits of using both qualitative and quantitative methods for evaluation
HCI	the implications and broader impacts of a given design
HCI	Pre-register a study design, with planned statistical tests
HCI	Prototyping techniques and tools
HCI	patterns
HCI	constraints
HCI	patterns and guidelines
HCI	processes
HCI	Interaction techniques
HCI	Visual UI design
HCI	Immersive environments
HCI	3D printing and fabrication
HCI	Asynchronous interaction models
HCI	Creativity support tools
HCI	Voice UI designs
HCI	Propose system designs tailored to a specified appropriate mode of interaction
HCI	Follow an iterative design and development process that incorporates the following:
HCI	the impact of changing constraints and design tradeoffs on
HCI	architectural design approaches in the context of project goals
HCI	synchronization challenges as part of the user experience in distributed environments
HCI	and compare the privacy implications behind different input techniques for a given
HCI	the rationale behind a UI design based on visual design principles
HCI	the privacy implications within a VR/AR/MR scenario
HCI	Universal and user-centered design
HCI	Accountability
HCI	Accessibility and inclusive design
HCI	Evaluating the design
HCI	System design
HCI	Participatory and inclusive design processes
HCI	Evaluating the design: Implications and impacts of design: with respect to the environment
HCI	VR/AR/MR scenarios
HCI	Conduct a user-centered design process that is integrated into a project
HCI	and critique the potential impacts of a design on society and relevant communities to
HCI	Evaluating the design: Identify the implications and broader impacts of a given design
HCI	the privacy implications within a VR/AR/MR scenario
MSF	Sets, relations, functions, cardinality
MSF	Recursive mathematical definitions
MSF	Proof techniques
MSF	Permutations, combinations, counting, pigeonhole principle
MSF	Modular arithmetic
MSF	Logic: truth tables, connectives, inference rules, formulas, normal forms, simple
MSF	Graphs: basic definitions
MSF	Order notation
MSF	Sets, Relations, and Functions, Cardinality
MSF	Permutations, combinations, and counting
MSF	Logic
MSF	Graphs
MSF	Basic notions: sample spaces, events, probability, conditional probability, Bayes rule
MSF	Discrete random variables and distributions
MSF	Continuous random variables and distributions
MSF	Expectation, variance, law of large numbers, central limit theorem
MSF	Conditional distributions and expectation
MSF	Applications to computing, the difference between probability and statistics
MSF	Applications to computing
MSF	Univariate data: point estimation, confidence intervals
MSF	Multivariate data: estimation, correlation, regression
MSF	Data transformation: dimension reduction, smoothing
MSF	Statistical models and algorithms
MSF	Hypothesis testing
MSF	Sampling, bias, adequacy of samples, Bayesian vs frequentist interpretations
MSF	Solving equations, row-reduction
MSF	Linear independence, span, basis
MSF	Orthogonality, projection, least-squares, orthogonal bases
MSF	Linear combinations of polynomials, Bezier curves
MSF	Eigenvectors and eigenvalues
MSF	Applications to computer science: Principal Components Analysis, Singular Value
MSF	Vectors: definitions, vector operations, geometric interpretation, angles
MSF	Applications to computer science: PCA, SVD, page-rank, graphics
MSF	Sequences, series, limits
MSF	Single-variable derivatives: definition, computation rules, derivatives of important
MSF	Parametric and polar representations
MSF	Taylor series
MSF	Multivariate calculus: partial derivatives, gradient, chain-rule, vector valued functions
MSF	CS applications: gradient descent for machine learning, forward and inverse kinematics
MSF	ODEs: definition, Euler method, applications to simulation
NC	Importance of networking in contemporary computing, and associated challenges
NC	Switching techniques
NC	Layers and their roles
NC	Layering principles
NC	Network elements
NC	Basic queueing concepts
NC	Articulate the organization of the internet
NC	and define the appropriate network terminology
NC	the layered structure of a typical networked architecture
NC	the different types of complexity in a network
NC	Naming and address schemes
NC	Distributed application paradigms
NC	Diversity of networked application demands (See
NC	Coverage of application-layer protocols
NC	Interactions with TCP, UDP, and Socket APIs
NC	the principles of naming, addressing, resource location
NC	the needs of specific networked application demands
NC	the details of one application layer protocol
NC	a simple client-server socket-based application
NC	Unreliable delivery
NC	Principles of reliability
NC	Error control
NC	Flow control
NC	Congestion control
NC	TCP and performance issues
NC	the operation of reliable delivery protocols
NC	the factors that affect the performance of reliable delivery protocols
NC	some TCP reliability design issues
NC	and implement a simple reliable protocol
NC	Forwarding methods
NC	IP and Scalability issues
NC	various routing paradigms and hierarchies
NC	how packets are forwarded in an IP network
NC	how the Internet tackles scalability challenges
NC	Introduction to modulation, bandwidth, and communication media
NC	Encoding and Framing
NC	Medium Access Control
NC	Ethernet and WiFi
NC	Switching
NC	Local Area Network Topologies
NC	some basic aspects of modulation, bandwidth, and communication media
NC	in detail a MAC protocol
NC	understanding of encoding and framing solution tradeoffs
NC	details of the implementation of Ethernet
NC	how switching works
NC	one kind of a LAN topology
NC	General intro about security
NC	Countermeasures
NC	some of the threat models of network security
NC	specific network-based countermeasures
NC	various aspects of network security from a case study
NC	Principles of cellular communication
NC	Principles of Wireless LANs
NC	Device to device communication
NC	Multi-hop wireless networks
NC	some aspects of cellular communication such as registration
NC	how 802.11 supports mobile users
NC	practical uses of device-to-device communication, as well as multihop
NC	one type of mobile network such as ad hoc
NC	Network Virtualization
NC	Quantum Networking
NC	Satellite, mmWave, Visible Light
NC	the value of advances in middleboxes in networks
NC	the importance of Software Defined Networks
NC	some of the added value achieved by using Quantum Networking
OS	Influences of security, networking, multimedia, parallel and distributed computing
OS	Exposure of operating systems functions in shells and systems programming
OS	Understand the objectives and functions of modern operating systems
OS	the design issues in different usage scenarios
OS	Understand the functions of a contemporary operating system with respect to convenience
OS	Operating system software design and approaches (e.g., monolithic, layered, modular, micro
OS	Abstractions, processes, and resources
OS	Concept of system calls and links to application program interfaces. (See
OS	The evolution of the link between hardware architecture and the operating system functions
OS	Protection of resources means protecting some machine instructions/functions
OS	Leveraging interrupts from hardware level: service routines and implementations
OS	Performance costs of context switches and associated cache flushes when performing process
OS	Understand how the application of software design approaches to operating systems
OS	Categorize system calls by purpose
OS	Understand dynamics of invoking a system call
OS	whether a function can be implemented in the application layer or can only be
OS	Understand how the separation into kernel and user mode affects safety and performance
OS	Understand the advantages and disadvantages of using interrupt processing in enabling
OS	Thread abstraction relative to concurrency
OS	Race conditions, critical regions
OS	Deadlocks and starvation
OS	Multiprocessor issues
OS	Multiprocess concurrency vs multithreading
OS	Thread creation, states, structures
OS	Thread APIs
OS	Implementing thread safe code
OS	Race conditions in shared memory
OS	Understand concurrency issues in multiprocessor systems
OS	Overview of operating system security mechanisms
OS	Attacks and antagonism
OS	Review of major vulnerabilities in real operating systems
OS	Operating systems mitigation strategies such as backups
OS	Policy/mechanism separation
OS	Security methods and devices
OS	Protection, access control, and authentication
OS	Understand the requirement for protection and security mechanisms in operating systems
OS	and describe the attack vectors that leverage OS vulnerabilities
OS	Understand the mechanisms available in an OS to control access to resources
OS	the features and limitations of an operating system that impact protection and security
OS	Preemptive and non-preemptive scheduling
OS	Concepts of Symmetric Multi-Processor scheduling and cache coherence
OS	Timers
OS	Fairness and starvation
OS	Cooperative scheduling, such as Linux futexes and userland scheduling
OS	and contrast the common algorithms used for both preemptive and non-preemptive
OS	the relationships between scheduling algorithms and application domains
OS	the distinctions among types of processor scheduler such as short-term, medium-term
OS	a problem or solution to determine appropriateness for asymmetric and/or symmetric
OS	a problem or solution to determine appropriateness as a process vs threads
OS	some contexts benefitting from preemption and deadline scheduling
OS	Processes and threads relative to virtualization protected memory, process state, memory
OS	Memory footprint/segmentation
OS	Creating and loading executables, shared libraries, and dynamic linking
OS	Dispatching and context switching
OS	Interprocess communication (e.g., shared memory, message passing, signals, environment
OS	Understand how processes and threads use concurrency features to virtualize control
OS	the appropriate interprocess communication mechanism for a specific purpose in a
OS	Review of physical memory, address translation and memory management hardware
OS	Impact of memory hierarchy including cache concept, cache lookup, and per-CPU caching on
OS	Logical and physical addressing, address space virtualization
OS	Concepts of paging, page replacement, thrashing and allocation of pages and frames
OS	Allocation/deallocation/storage techniques performance and
OS	Security mechanisms and concepts in memory management including sandboxing, protection
OS	Virtual memory: leveraging virtual memory hardware for OS services and efficiency
OS	memory hierarchy and cost-performance tradeoffs
OS	the principles of virtual memory as applied to caching and paging
OS	the tradeoffs in terms of memory size
OS	the reason for and use of cache memory (performance and proximity, how caches
OS	how hardware is utilized for efficient virtualization
OS	Buffering strategies
OS	Direct Memory Access and polled I/O, Memory-mapped I/O
OS	Device interface abstractions, hardware abstraction layer
OS	Device driver purpose, abstraction, implementation, and testing challenges
OS	High-level fault tolerance in device communication
OS	architecture level device control implementation and link relevant operating system
OS	OS device management layers and the architecture (e.g., device controller, device driver
OS	the relationship between the physical hardware and the virtual devices maintained by the
OS	I/O data buffering and describe strategies for implementing it
OS	the advantages and disadvantages of direct memory access and discuss the
OS	the complexity and best practices for the creation of device drivers
OS	Concept of a file including data, metadata, operations, and access-mode
OS	File system mounting
OS	File access control
OS	File sharing
OS	Basic file allocation methods, including linked allocation table
OS	Allocation/deallocation/storage techniques impact on performance
OS	Free space management such as using bit tables vs linking
OS	Implementation of directories to segment and track file location
OS	the choices to be made in designing file systems
OS	different approaches to file organization, recognizing the strengths and weaknesses of
OS	software constructs appropriately given knowledge of the file system implementation
OS	File systems: partitioning, mount/unmount, virtual file systems
OS	In-depth implementation techniques
OS	Memory-mapped files
OS	Special-purpose file systems
OS	Naming, searching, access, backups
OS	Journaling and log-structured file systems
OS	Distributed file systems
OS	Encrypted file systems
OS	Fault tolerance
OS	how hardware developments have led to changes in the priorities for the design and the
OS	Map file abstractions to a list of relevant devices and interfaces
OS	and categorize different mount types
OS	the use of journaling and how log-structured file systems enhance fault tolerance
OS	purpose and complexity of distributed file systems
OS	examples of distributed file systems protocols
OS	mechanisms in file systems to improve fault tolerance
OS	Using virtualization and isolation to achieve protection and predictable performance
OS	Advanced paging and virtual memory
OS	Virtual file systems and virtual devices
OS	Containers and their comparison to virtual machines
OS	Thrashing
OS	Types of virtualizations
OS	Portable virtualization; emulation vs isolation
OS	Cost of virtualization
OS	Virtual machines and container escapes, dangers from a security perspective
OS	Hypervisors- hardware virtual machine extensions, hosts with kernel support, QEMU KVM
OS	how hardware architecture provides support and efficiencies for virtualization
OS	the difference between emulation and isolation
OS	virtualization tradeoffs
OS	hypervisors and the need for them in conjunction with different types of hypervisors
OS	Process and task scheduling
OS	Deadlines and real-time issues
OS	Low-latency vs soft real-time" vs "hard real time."
OS	Memory/disk management requirements in a real-time environment
OS	Failures, risks, and recovery
OS	Special concerns in real-time systems
OS	what makes a system a real-time system
OS	latency and its sources in software systems and its characteristics
OS	specific real time operating systems features and mechanisms
OS	Reliable and available systems
OS	Software and hardware approaches to address tolerance
OS	Spatial and temporal redundancy
OS	Methods used to implement fault tolerance
OS	Error identification and correction mechanisms, checksums of volatile memory in RAM
OS	File system consistency check and recovery
OS	Journaling and log-structured file systems
OS	Use-cases for fault-tolerance
OS	how operating systems can facilitate fault tolerance, reliability, and availability
OS	the range of methods for implementing fault tolerance in an operating system
OS	how an operating system can continue functioning after a fault occurs
OS	the performance and flexibility tradeoffs that impact using fault tolerance
OS	operating systems fault tolerance issues and mechanisms in detail
OS	Open source in operating systems
OS	End-of-life issues with sunsetting operating systems
OS	advantages and disadvantages of finding and addressing bugs in open-source kernels
OS	Contextualize history and positive and negative impact of Linux as an open-source product
OS	complications with reliance on operating systems past end-of-life
PDC	Parallelism
PDC	Distribution
PDC	Starting activities
PDC	Execution Properties
PDC	One or more of the following mappings and mechanisms across layered systems:
PDC	Graphically show) how to parallelize a compound numerical
PDC	why the concepts of consistency and fault tolerance do not arise in purely sequential
PDC	a function that efficiently counts events such as networking packet receptions
PDC	a filter/map/reduce program in multiple styles
PDC	a service that creates a thread to return a requested
PDC	Media
PDC	Channels
PDC	Memory
PDC	Data Stores
PDC	One or more of the following properties and extensions
PDC	the similarities and differences among: Party A sends a message on channel X with
PDC	a parallel program that requests data from multiple sites and summarizes them using some
PDC	the performance of buffered versus unbuffered versions of a producer-consumer
PDC	whether a given communication scheme provides sufficient security properties for a
PDC	Give an example of a scenario in which blocking message sends can deadlock
PDC	at least one design technique for avoiding liveness failures in programs using multiple
PDC	a program that illustrates memory-access or message reordering
PDC	the relative merits of optimistic versus conservative concurrency control under different
PDC	Give an example of a scenario in which an attempted optimistic update may never complete
PDC	Modify a concurrent system to use a more scalable, reliable, or available data store
PDC	Dependencies
PDC	Control constructs and design patterns
PDC	Atomicity
PDC	One or more of the following properties and extensions
PDC	Show how to avoid or repair a race error in a given program
PDC	a function that efficiently counts events such as sensor inputs or networking packet
PDC	a filter/map/reduce program in multiple styles
PDC	a program in which the termination of one set of parallel actions is followed by another
PDC	a program that speculatively searches for a solution by multiple activities, terminating
PDC	a program in which a numerical exception in one activity causes
PDC	a service that creates a thread to return a
PDC	Performance impact of design and implementation choices, including granularity, overhead
PDC	One or more of the following methods and tools:
PDC	how concurrent notions of safety and liveness extend their sequential counterparts
PDC	a set of invariants that must hold at each bulk-parallel step of a computation
PDC	a test program that can reveal a data race error; for example, missing an update when two
PDC	and measure behavior when a service is requested by unexpectedly many clients
PDC	and repair a performance problem due to sequential bottlenecks
PDC	Empirically compare throughput of two implementations of a common design (perhaps using an
PDC	and repair a performance problem due to communication or data latency
PDC	and repair a performance problem due to resource management overhead
PDC	and repair a reliability or availability problem
PDC	One of more of the following algorithmic domains
PDC	a parallel/distributed component based on a known algorithm
PDC	a data-parallel program that for example computes the average of an array of numbers
PDC	a producer-consumer program in which one component generates numbers, and another
PDC	Choose among different parallel/distributed designs for components of a given system
PDC	the performance and energy efficiency of multiple implementations of a similar design, for
PDC	Programs: KA Core on threads, tasks, instruction-level parallelism
PDC	Communication: KA Core on multicore architectures, memory, concurrent data stores
PDC	Evaluation: KA Core on performance analysis
PDC	Algorithms: project-based KA Core coverage of data processing and resource management
PDC	SDF-Fundamentals: Fundamental Programming Concepts and Practices  This knowledge unit
PDC	SDF-Data-Structures: Fundamental Data Structures  This knowledge unit aims to develop core
PDC	SDF-Practices: Software Development Practices  This knowledge unit develops the core
SDF	Basic concepts such as variables, primitive data types, expressions, and their evaluation
SDF	Key modularity constructs such as functions (and methods and classes, if supported in the
SDF	Input and output using files and APIs
SDF	Libraries and frameworks provided by the language
SDF	Recursion
SDF	Dealing with runtime errors in programs
SDF	Basic concepts of programming errors, testing, and debugging
SDF	Documenting/commenting code at the program and module level
SDF	a security mindset
SDF	programs that use the fundamental programming constructs: assignment and expressions
SDF	programs using functions with parameter passing
SDF	programs that effectively use the different structured data types provided in the language
SDF	programs that use file I/O to provide data persistence across multiple executions
SDF	programs that use language-provided libraries and frameworks
SDF	programs that use APIs to access or update data
SDF	programs that create simple classes and instantiate objects of those classes (if supported
SDF	the concept of recursion and identify when and how to use it effectively
SDF	recursive functions
SDF	programs that can handle runtime errors
SDF	a given program and explain what it does
SDF	comments for a program or a module specifying what it does
SDF	the flow of control during the execution of a program
SDF	appropriate terminology to identify elements of a program
SDF	Selecting and using appropriate data structures
SDF	Performance implications of choice of data structure
SDF	Strings and string processing
SDF	the appropriate data structure for a given problem
SDF	how the performance of a program may change when using different data structures or
SDF	Concept of algorithm and notion of algorithm efficiency
SDF	Some common algorithms
SDF	Impact of algorithms on time-space efficiency of programs
SDF	the role of algorithms for writing programs
SDF	how a problem may be solved by different algorithms, each with different properties
SDF	the impact on space/time performance of some algorithms
SDF	Basic testing, including test case design
SDF	of a general-purpose IDE, including its debugger
SDF	Programming style that improves readability
SDF	Specifying functionality of a module in a natural language
SDF	tests for modules and apply a variety of strategies to design test cases
SDF	some limitations of testing programs
SDF	Build, execute, and debug programs using a modern IDE and associated tools such as visual
SDF	basic programming style guidelines to aid readability of programs such as comments
SDF	specifications of a module as module comment describing its functionality
SDF	Intellectual property rights of programmers for programs they develop
SDF	Plagiarism and academic integrity
SDF	Responsibility and liability of programmers regarding code they develop for solutions
SDF	Basic professional work ethics of programmers
SDF	Explain/understand some of the intellectual property issues relating to programs
SDF	Explain/understand when code developed by others can be used and proper ways of disclosing
SDF	Explain/understand one or more codes of conduct applicable to programmers
SDF	SDF-Fundamentals
SDF	SDF-Data-Structures
SDF	SDF-Algorithms
SDF	SDF-Practices
SDF	SDF-SEP
SDF	SE-Design: While Product Requirements focus on the user-facing functionality of a software
SDF	SE-Refactoring: Refactoring and Code Evolution focuses on refactoring and maintenance
SDF	SE-Formal: Formal Methods provides mathematically rigorous mechanisms to apply to software
SE	Common causes of team conflict, and approaches for conflict resolution
SE	Cooperative programming:
SE	Roles and responsibilities in a software team:
SE	Importance of team diversity and inclusivity
SE	Interfacing with stakeholders, as a team:
SE	Follow effective team communication practices
SE	Facilitate a conflict-resolution and problem-solving strategy in a team setting
SE	Collaborate effectively in cooperative development/programming
SE	Propose and delegate necessary roles and responsibilities in a software development team
SE	Compose and follow an agenda for a team meeting
SE	Promote the importance of and benefits that diversity and inclusivity brings to a software
SE	Software configuration management and version control:
SE	Release management
SE	Testing tools including static and dynamic analysis tools
SE	Software process automation:
SE	and communication tools
SE	Tool integration concepts and mechanisms
SE	of modern IDE facilities  debugging, refactoring, searching/indexing, ML-powered code
SE	the difference between centralized and distributed software configuration management
SE	how version control can be used to help manage software release management
SE	configuration items and use a source code control tool in a small team-based project
SE	how available static and dynamic test tools can be integrated into the software
SE	the capability to use software tools in support of the development of a software
SE	functional requirements using, for example, use cases or user stories
SE	Properties of requirements including consistency, validity, completeness, and feasibility
SE	Requirements elicitation
SE	Communicating and/or formalizing requirement specifications
SE	Prototyping a tool for both eliciting and validating/confirming requirements
SE	Effort estimation:
SE	different methods of eliciting requirements along multiple axes
SE	differences between two methods of describing functional requirements (e.g., customer
SE	Collect a set of requirements for a simple software system
SE	areas of a software system that need to be changed, given a description of the system and
SE	the functional and non-functional requirements in a set of requirements
SE	a prototype of a software system to validate a set of requirements  building a mock-up
SE	an implementation sequence for a set of tasks, adhering to dependencies between
SE	a requirement specification for a simple software system
SE	System design principles
SE	Software architecture
SE	Programming in the large vs programming in the small
SE	Code smells and other indications of code quality, distinct from correctness
SE	API design principles
SE	Identifying and codifying data invariants and time invariants
SE	Structural and behavioral models of software designs
SE	Data design
SE	Requirement traceability
SE	modeling, for instance with class diagrams, entity relationship diagrams, or sequence
SE	Measurement and analysis of design quality
SE	Principles of secure design and coding
SE	Evaluating design tradeoffs
SE	the standard software architecture of a given high-level design
SE	and use an appropriate design paradigm to design a simple software system and explain
SE	Adapt a flawed system design to better follow principles such as separation of concerns or
SE	the dependencies among a set of software components in an architectural design
SE	an API for a single component of a large software system, including identifying and
SE	an API description in terms of consistency, composability, and expandability
SE	Expand an existing design to include a new piece of functionality
SE	a set of data structures to implement a provided API surface
SE	which requirements are satisfied by a provided software design
SE	a natural language software design into class diagrams
SE	Contrast two software designs across different qualities, such as efficiency or usability
SE	Practical small-scale testing
SE	Documentation
SE	Coding style
SE	Debugging
SE	Logging
SE	of libraries and frameworks developed by others
SE	Larger-scale testing
SE	Work sequencing, including dependency identification, milestones, and risk retirement
SE	Potential security problems in programs
SE	Development context: green field vs existing code base
SE	Release management
SE	DevOps practices
SE	appropriate unit tests for a small component
SE	appropriate interface and implementation comments for a small component
SE	techniques, coding idioms and mechanisms for implementing designs to achieve desired
SE	robust code using exception handling mechanisms
SE	secure coding and defensive coding practices
SE	and use a defined coding standard in a small software project
SE	and contrast integration strategies including top-down, bottom-up, and sandwich
SE	the process of analyzing and implementing changes to code base developed for a specific
SE	the process of analyzing and implementing changes to a large existing code base
SE	a software component that performs some non-trivial task and is resilient to input and run
SE	Verification and validation concepts
SE	Why testing matters: Does the component remain functional as the code evolves?
SE	Testing objectives
SE	Test kinds
SE	Stylistic differences between tests and production code: DAMP vs DRY  more duplication is
SE	Test planning and generation
SE	Test development
SE	Verification and validation in the development cycle
SE	Domain specific verification and validation challenges
SE	Verification and validation tooling and automation
SE	Performance testing and benchmarking
SE	Testing asynchronous, parallel, and concurrent systems
SE	Verification and validation of non-code artifacts
SE	why testing is important
SE	Distinguish between program validation and verification
SE	different objectives of testing
SE	and contrast the different types and levels of testing (regression, unit, integration
SE	techniques for creating a test plan and generating test cases
SE	a test plan for a medium-size code segment which includes a test matrix and generation of
SE	a test plan for a medium-size code segment
SE	the fundamental principles of test-driven development methods and explain the role of
SE	issues involving the testing of object-oriented software
SE	mocking and dependency injection and their application
SE	Undertake, as part of a team activity, a code review of a medium-size code segment
SE	the role that tools can play in the validation of software
SE	Automate the testing in a small software project
SE	the roles, pros, and cons of pre-commit and post-commit testing
SE	the tradeoffs between test coverage and test throughput/latency and how this can impact
SE	a defect tracking tool to manage software defects in a small software project
SE	the limitations of testing in certain domains
SE	and compare different tools for verification and validation
SE	Automate the use of different tools in a small software project
SE	how and when random numbers should be used in testing
SE	approaches for fault estimation
SE	throughput and latency and provide examples of each
SE	speedup and the different forms of scaling and how they are computed
SE	common performance bottlenecks
SE	statistical methods and best practices for benchmarking software
SE	techniques for and challenges with measuring time when constructing a benchmark
SE	techniques and issues with testing asynchronous, concurrent, and parallel software
SE	a test plan for a medium-size code segment which contains asynchronous, concurrent
SE	techniques for the verification and validation of non-code artifacts
SE	Hyrums Law/The Law of Implicit Interfaces
SE	Backward compatibility
SE	Refactoring
SE	Versioning
SE	changes that can be broadly considered backward compatible, potentially with explicit
SE	whether a proposed change is sufficiently safe given the versioning methodology in use
SE	Plan a complex multi-step refactoring to change default behavior of an API safely
SE	Identifying reliability requirements for different kinds of software
SE	Software reliability, system reliability and failure behavior
SE	Defect injection and removal cycle, and different approaches for defect removal
SE	the error budget approach to reliability with the error-free approach and identify
SE	Software reliability models
SE	Software fault tolerance techniques and models
SE	Measurement-based analysis of software reliability  telemetry, monitoring and alerting
SE	how to determine the level of reliability required by a software system
SE	the problems that exist in achieving very high levels of reliability
SE	the ability to apply multiple methods to develop reliability estimates for a software
SE	ways to apply redundancy to achieve fault tolerance
SE	single-point-of-failure dependencies in a system design
SE	Formal specification of interfaces
SE	Problem areas well served by formal methods
SE	Comparison to other tools and techniques for defect detection
SE	Formal approaches to software modeling and analysis
SE	the role formal specification and analysis techniques can play in the development of
SE	formal specification and analysis techniques to software designs and programs with low
SE	the potential benefits and drawbacks of using formal specification languages
SE	Basic concepts t3 of authentication and authorization/access control
SE	Vulnerabilities, threats, attack surfaces, and attack vectors
SE	Denial of Service and Distributed Denial of Service
SE	Access control models
SE	Security controls
SE	Concepts of trust and trustworthiness
SE	Applications of a security mindset: web, cloud, and mobile devices
SE	Protecting embedded and cyber-physical systems
SE	Principles of usable security and human-centered computing
SE	Security risks in building and operating AI/machine learning systems (e.g., algorithm bias
SE	Hardware considerations in security, e.g., principles of secure hardware, secure processor
SE	a system for possible attacks that can be launched by an adversary
SE	and develop approaches to protect a system from a set of identified threats
SE	how harm to user privacy can be avoided
SE	a system that incorporates various principles of security and privacy
SE	the different access control models in terms of functionality and performance
SE	hardware vulnerabilities that can impact software
SEC	Principles and practices of privacy
SEC	Societal impacts on breakdowns in security and privacy
SEC	Applicability of laws and regulations on security and privacy
SEC	Security by design
SEC	Privacy by design and privacy engineering
SEC	Societal impacts of Internet of Things devices and other emerging technologies on security
SEC	Calculate the impact of a breakdown in security of a given system
SEC	a system that conforms to security laws
SEC	a set of privacy regulations to design a system that protects privacy
SEC	the legal ramifications of a system not corresponding to applicable laws and regulations
SEC	a system that is designed to avoid harm to user privacy
SEC	Common vulnerabilities and weaknesses
SEC	SQL injection and other injection attacks
SEC	Cross-site scripting techniques and mitigations
SEC	Input validation and data sanitization
SEC	Type safety and type-safe languages
SEC	Buffer overflows, stack smashing, and integer overflows
SEC	Security issues due to race conditions
SEC	Principles of noninterference and nondeducibility
SEC	Preventing information flow attacks
SEC	Offensive security techniques as a defense
SEC	AI-assisted malware detection techniques
SEC	Ransomware: creation, prevention, and mitigation
SEC	Secure use of third-party components
SEC	Malware: varieties, creation, reverse engineering, and defense against them
SEC	Assurance: testing, verification, and validation
SEC	Static and dynamic analyses
SEC	Secure compilers and secure code generation
SEC	underlying problems in given examples of an enumeration of common weaknesses and
SEC	input validation and data sanitization techniques to enhance security of a program
SEC	how the selection of a programming language can impact the security of the system being
SEC	Rewrite a program in a type-safe language originally written in an unsafe
SEC	a program for possible buffer overflow attacks and rewrite to prevent such attacks
SEC	a set of related programs for possible race conditions and prevent an adversary from
SEC	and prevent SQL injections attacks on a database application
SEC	and prevent cross-site scripting attacks against a website
SEC	different kinds of malicious software
SEC	a program that tests for all input handling errors
SEC	a system that is protected from unauthorized information flows
SEC	static and dynamic tools to identify programming faults
SEC	a system for the existence of malware and remove it
SEC	preventive techniques to reduce the occurrence of ransomware
SEC	Differences between algorithmic, applied, and mathematical views of cryptography
SEC	Basic cryptography: symmetric key and public key cryptography
SEC	Basic cryptographic building blocks, including symmetric encryption, asymmetric encryption
SEC	Kerckhoffs principle and use of vetted libraries
SEC	Additional mathematics: primality, factoring, and elliptic curve cryptography
SEC	Public-key cryptosystems: Diffie-Hellman and RSA
SEC	Data integrity and authentication: hashing, and digital signatures
SEC	Cryptographic protocols: challenge-response authentication, zero-knowledge protocols
SEC	Attacker capabilities: chosen-message attack, birthday attacks, side channel
SEC	Quantum cryptography; Post Quantum/Quantum resistant cryptography
SEC	Blockchain and cryptocurrencies
SEC	the role of cryptography in supporting security and privacy
SEC	the risks of inventing ones own cryptographic methods
SEC	the importance of prime numbers in cryptography and explain their use in cryptographic
SEC	and cryptanalyze classical ciphers
SEC	how crypto keys can be managed securely
SEC	the space and time performance of a given set of cryptographic methods
SEC	how modern private-key cryptosystems work and ways to cryptanalyze them
SEC	how modern public-key cryptosystems work and ways to cryptanalyze them
SEC	different cryptographic algorithms in terms of security
SEC	key exchange protocols and show approaches to reduce their failure
SEC	real-world applications of cryptographic primitives and protocols
SEC	how quantum cryptography works and the impact of quantum computing on cryptographic
SEC	Problem analysis and situational analysis to address system security
SEC	Security design and engineering, including functional requirements, security subsystems
SEC	Security attack domains and attack surfaces, e.g., communications and networking, hardware
SEC	Attestation of software products with respect to their specification and adaptiveness
SEC	and development of cyber-physical systems
SEC	a threat model for a system or system design
SEC	situational analysis to develop secure solutions under a specified scenario
SEC	a given scenario for tradeoff analysis for system performance, risk assessment, and costs
SEC	a set of technical security controls, countermeasures, and information protections to meet
SEC	the effectiveness of security functions, technical controls, and componentry for a system
SEC	and mitigate security vulnerabilities and weaknesses in a system
SEC	and predict emergent behavior in areas such as Data Science, AI, and Machine Learning
SEC	Basic principles and methodologies for digital forensics
SEC	System design for forensics
SEC	Attacks on forensics and preventing such attacks
SEC	Incident handling processes
SEC	Rules of evidence  general concepts and differences between jurisdictions
SEC	what a digital investigation is and how it can be implemented
SEC	and implement software to support forensics
SEC	legal requirements for using seized data and its usage
SEC	and implement an end-to-end chain of custody from initial digital evidence seizure to
SEC	Extract data from a hard drive to comply with the law
SEC	Recover data based on a given search term from an imaged system
SEC	Capture and analyze network traffic
SEC	approaches to address the challenges associated with mobile device forensics
SEC	forensics tools to investigate security breaches
SEC	and mitigate anti-forensic methods
SEC	Protecting critical assets from threats
SEC	Security governance: organizational objectives and general risk assessment
SEC	Security management: achieve and maintain appropriate levels of confidentiality, integrity
SEC	Approaches to identifying and mitigating risks to computing infrastructure
SEC	critical assets and how they can be protected
SEC	between security governance, management, and controls, giving examples of each
SEC	a technical control and implement it to mitigate specific threats
SEC	and assess risk of programs and database applications causing breaches
SEC	and implement appropriate backup strategies conforming to a given policy
SEC	a breach disclosure policy based on legal requirements and implement the policy
SEC	the risks and benefits of outsourcing to the cloud
SEP	Social implications in a hyper-networked world where the
SEP	Impact of computing applications on individual
SEP	Growth and control of the internet, data, computing, and artificial intelligence
SEP	Context-aware computing
SEP	the different ways that computer technology (networks, mobile computing, artificial
SEP	developers assumptions and values embedded in hardware and software design
SEP	Interpret the social context of a given design and its implementation
SEP	the efficacy of a given design and implementation using empirical data
SEP	Understand the implications of technology use for different identities, cultures
SEP	the internets role in facilitating communication between citizens, governments, and each
SEP	the effects of reliance on computing in the implementation of democracy (e.g., delivery of
SEP	the impact of a lack of appropriate representation of people from historically minoritized
SEP	the implications of context awareness in ubiquitous computing systems
SEP	Express how access to the internet and computing technologies affect different societies
SEP	why/how internet access can be viewed as a human right
SEP	Avoiding fallacies and misrepresentation in argumentation
SEP	Ethical theories and decision-making
SEP	Professional checklists
SEP	Evaluation rubrics
SEP	Stakeholder analysis
SEP	Standpoint theory
SEP	Introduction to ethical frameworks (e.g., consequentialism such as utilitarianism, non
SEP	how a given cultural context impacts decision making
SEP	Express the use of example and analogy in ethical argument
SEP	basic logical fallacies in an argument
SEP	an argument to identify premises and conclusion
SEP	how and why ethics is so important in computing and how it relates to cultural norms
SEP	a decision made on ethical grounds
SEP	the advantages and disadvantages of traditional ethical frameworks
SEP	ethical dilemmas related to the creation and use of technology from multiple perspectives
SEP	Community values and the laws by which we live
SEP	Introduction to theories describing the human creation and use of technology including
SEP	The role of the computing professional and professional societies in public policy
SEP	Maintaining awareness of consequences
SEP	Ethical dissent and whistleblowing
SEP	The relationship between regional culture and ethical dilemmas
SEP	Dealing with harassment and discrimination
SEP	Forms of professional credentialing
SEP	Ergonomics and healthy computing environments
SEP	Time-to-market and cost considerations versus quality professional standards
SEP	ethical issues that arise in software design, development practices, and software
SEP	how to address ethical issues in specific situations
SEP	the mechanisms that typically exist for a professional to keep up to date in ethical
SEP	the strengths and weaknesses of relevant professional codes as expressions of being a
SEP	a global computing issue, observing the role of professionals and government officials in
SEP	ways in which professionals and professional organizations may contribute to public
SEP	the consequences of inappropriate professional behavior
SEP	examples of how regional culture interplays with ethical dilemmas
SEP	forms of harassment and discrimination and avenues of assistance
SEP	Assess various forms of professional credentialing
SEP	State the relationship between ergonomics in computing environments and peoples health
SEP	issues associated with industries push to focus on time-to-market versus enforcing
SEP	Intellectual property rights
SEP	Intangible digital intellectual property
SEP	Legal foundations for intellectual property protection
SEP	Common software licenses
SEP	Plagiarism and authorship
SEP	Philosophical foundations of intellectual property
SEP	Forms of intellectual property and the rights
SEP	Limitations on copyright protections, including fair use and the first sale doctrine
SEP	Intellectual property laws and treaties that impact the enforcement of copyrights
SEP	Moral and legal foundations of the open-source movement
SEP	Systems that use others data
SEP	and critique legislation and precedent aimed at digital copyright infringements
SEP	contemporary examples of intangible digital intellectual property
SEP	an appropriate software license for a given project
SEP	Defend legal and ethical uses of copyrighted materials
SEP	Interpret the intent and implementation of software licensing
SEP	whether a use of copyrighted material is likely to be fair use
SEP	the ethical issues inherent in various plagiarism detection mechanisms
SEP	the philosophical bases of intellectual property in an appropriate context
SEP	Distinguish the conflicting issues involved in securing software patents
SEP	the rationale for the legal protection of intellectual property in the appropriate context
SEP	the use of copyrighted work under the concepts of fair use and the first sale doctrine
SEP	the goals of the open-source movement and its impact on fields beyond computing, such
SEP	the global nature of software piracy
SEP	Criticize the use of technical measures of digital rights management (e.g., encryption
SEP	the nature of anti-circumvention laws in the context of copyright protection
SEP	Conceptions of anonymity, pseudonymity, and identity
SEP	Civil liberties, privacy rights, and cultural differences
SEP	Legal foundations of privacy protection in relevant jurisdictions
SEP	Privacy legislation in areas of practice
SEP	Freedom of expression and its limitations
SEP	User-generated content, content moderation, and liability
SEP	solutions to privacy threats in transactional databases and data warehouses
SEP	the role of data collection in the implementation of pervasive surveillance systems (e.g
SEP	Distinguish the concepts and goals of anonymity and pseudonymity
SEP	the ramifications of technology-based privacy protections, including differential privacy
SEP	the philosophical basis for the legal protection of personal privacy in an appropriate
SEP	strategies to enable appropriate freedom of expression
SEP	Oral, written, and electronic team and group communication
SEP	Communicating with different stakeholders such as customers, leadership, or the public
SEP	Team collaboration and conflict resolution
SEP	Accessibility and inclusivity requirements for addressing professional audiences
SEP	Tradeoffs in competing factors that affect communication channels and choices
SEP	Communicating to solve problems or make recommendations in the workplace, such as raising
SEP	written technical documentation for technical accuracy, concision, lack of ambiguity, and
SEP	Compose and deliver an audience-aware, accessible, and organized formal presentation
SEP	Plan interactions with others in ways that invite
SEP	and describe qualities of effective communication (e.g., virtual, face-to-face, intragroup
SEP	ways to influence performance and results in diverse and cross-cultural teams
SEP	Assess personal strengths and weaknesses to work remotely as part of a team drawing from
SEP	Choose an appropriate way to communicate delicate ethical concerns
SEP	Guidelines for sustainable design standards
SEP	ways to be a sustainable practitioner in a specific area or with a specific project
SEP	Assess the environmental impacts of a given projects deployment (e.g., energy consumption
SEP	global social and environmental impacts of computer use and disposal
SEP	the sustainable effects of modern practices and activities (e.g., remote work, e-commerce
SEP	the environmental impacts of design choices within the field of computing that relate to
SEP	the social and environmental impacts of new system designs
SEP	guidelines for sustainable IT design or deployment in areas such as smart energy systems
SEP	The history of computing: hardware, software, and human/organizational
SEP	Age I: Ancient analog computing (Stonehenge, Antikythera mechanism, Salisbury
SEP	Age II: ENIAC, UNIVAC, Bombes
SEP	Age III: PCs, modern computer hardware and software, Moores Law
SEP	Age IV: Networking, internet architecture, browsers and their evolution, standards, born
SEP	Age V: Mobile computing and smartphones, cloud computing and models thereof
SEP	Age VI: Decision making systems, recommender systems, generative AI and other machine
SEP	how perspectives held today have been shaped by history, and that alternative
SEP	formative and consequential trends in the history of the computing field
SEP	the contributions of pioneering individuals or organizations (research labs, computer
SEP	the historical context for important moments in history of computing, such as the move
SEP	daily life before and after the advent of milestone developments (e.g., personal
SEP	Economic models: regulated and unregulated, monopolies, network effects, and open market;
SEP	Pricing and deployment strategies: planned obsolescence, subscriptions, freemium, software
SEP	Automation, AI, and their effects on job markets, developers, and users
SEP	Ethical concerns surrounding the attention economy and other economies of computing (e.g
SEP	the social effects of economic models
SEP	examples of digital divides
SEP	Understand the effects of automation and AI on society
SEP	Understand the ethical implications of computing economies that rely on attention and data
SEP	Computer crimes, legal redress for computer criminals and impact on victims and society
SEP	Social engineering, computing-enabled fraud, identity theft and recovery from these
SEP	Cyber terrorism, criminal hacking, and hacktivism
SEP	Malware, viruses, worms
SEP	Attacks on critical infrastructure such as electrical grids and pipelines
SEP	Non-technical fundamentals of security
SEP	Benefits and challenges of existing and proposed computer crime laws
SEP	Security policies and the challenges of change and compliance
SEP	Responsibility for security throughout the computing life cycle
SEP	International and local laws and how they intersect
SEP	classic examples of computer crimes and social engineering incidents with societal impact
SEP	issues with laws that apply to computer crimes
SEP	the motivation and ramifications of cyber terrorism, data theft, hacktivism, ransomware
SEP	the professional's role in security and the tradeoffs and challenges involved
SEP	Investigate measures that can be taken by both individuals and organizations including
SEP	a company-wide security policy, which includes procedures for managing passwords and
SEP	The benefits of diverse development teams and the impacts of teams that are not diverse
SEP	Inclusive language and charged terminology, and why their use matters
SEP	Inclusive behaviors and why they matter
SEP	Designing and developing technology with accessibility in mind
SEP	and distinguish equity, equality, diversity, inclusion, and accessibility
SEP	language, practices, and behaviors that may make someone feel included in a workplace
SEP	the accessibility of your classroom or lab. Evaluate the accessibility of your webpage
SEP	collegiality and respect when working with team members who do not share your
SEP	the demographics of your institutions computer science and STEM majors to the overall
SEP	developers assumptions and values embedded in hardware and software design
SEP	examples of the benefits that diverse teams can bring to software products, and how a lack
SEP	the work of experts who reflect the identities of the classroom and the world
SEP	examples of systemic changes that could positively address diversity, equity, inclusion
SEP	the demographics of your institution to the overall community demographics. If they
SF	Hardware as a computational paradigm: Fundamental logic building blocks; Logic expressions
SF	Programming abstractions, interfaces, use of libraries
SF	Distinction and interaction between application and OS services, remote procedure call
SF	Basic concept of pipelining, overlapped processing stages
SF	Basic concept of scaling: performance vs problem size
SF	the basic building blocks of computers and their role in the historical development of
SF	how computing systems are constructed of layers upon layers, based on separation of
SF	that hardware, OS, VM, and application are additional layers of interpretation/processing
SF	the mechanisms of how errors are detected, signaled back, and handled through the
SF	a simple program using methods of layering, error detection
SF	bugs in a layered program by using tools for program tracing, single stepping, and
SF	Digital vs Analog/Discrete vs Continuous Systems
SF	Simple logic gates, logical expressions, Boolean logic simplification
SF	Clocks, State, Sequencing
SF	State and state transition
SF	Finite state machines
SF	Combinational Logic, Sequential Logic, Registers, Memories
SF	Computers and Network Protocols as examples of State Machines
SF	Sequential vs parallel processing
SF	Application-level sequential processing: single thread
SF	Simple application-level parallel processing: request level
SF	the differences between digital and analog systems, and between discrete and continuous
SF	computations as a system characterized by a known set of configurations with transitions
SF	the distinction between systems whose output is only a function of their input
SF	state machine descriptions for simple problem statement solutions (e.g., traffic light
SF	a computer as a state machine that interprets machine instructions
SF	how a program or network protocol can also be expressed as a state machine and that
SF	a simple sequential problem and a simple parallel version of the same program
SF	the performance of simple sequential and parallel versions of a program with different
SF	on an execution timeline how parallelism events and operations can take place
SF	Different types of resources
SF	Advantages and disadvantages of common scheduling algorithms
SF	how finite computer resources (e.g., processor share, memory, storage, and network
SF	how common resource allocation/scheduling algorithms work
SF	common scheduling algorithms and evaluate their performances
SF	the pros and cons of common scheduling algorithms
SF	Latencies in computer systems
SF	Introduction to the processor memory hierarchy
SF	The formula for average memory access time
SF	Rationale of virtualization and isolation: protection and predictable performance
SF	Methods for implementing virtual memory and virtual machines
SF	the breakdown of the latency of computer systems in terms of memory, disk, and network
SF	the importance of locality in determining system performance
SF	Calculate average memory access time and describe the tradeoffs in memory hierarchy
SF	why it is important to isolate and protect the execution of individual programs and
SF	how the concept of indirection can create the illusion of a dedicated machine and its
SF	the performance of two application instances running on separate virtual machines and
SF	Performance figures of merit
SF	CPI equation as a tool for understanding tradeoffs in the design of
SF	Order of magnitude analysis
SF	Analysis of slow and fast paths of a system
SF	Events on their effect on performance
SF	Analytical tools to guide quantitative evaluation
SF	Microbenchmark pitfalls
SF	how the components of system architecture contribute to improving its performance
SF	the circumstances in which a given figure of a system performance metric is useful
SF	the usage and inadequacies of benchmarks as a measure of system performance
SF	Amdahls law and discuss its limitations
SF	limit studies or simple calculations to produce order-of-magnitude estimates for a given
SF	software tools to profile and measure program performance
SF	and conduct a performance-oriented experiment of a common system (e.g., an OS and
SF	a performance experiment on a layered system to determine the effect of a system
SF	Distinction between bugs, faults, and failures
SF	Reliability vs availability
SF	Reliability through redundancy
SF	Other approaches to reliability
SF	simple algorithms for exploiting redundant information for the purposes of data correction
SF	different error detection and correction methods for their data overhead, implementation
SF	Common system security issues (See
SF	Countermeasures
SF	Representative countermeasure systems
SF	some common system security issues and give examples
SF	some countermeasures against system security issues
SF	Common criteria of system design (See
SF	Designs of representative systems
SF	common criteria of system design
SF	the design of some representative systems
SF	Intellectual property rights of computer systems
SF	Common software licenses
SF	Computer crimes
SF	the intellectual property rights of computer systems
SF	representative software licenses and compare their differences
SF	representative computer crimes
SPD	Overview of development platforms
SPD	Programming via platform-specific Application Programming Interface vs traditional
SPD	Overview of platform Languages
SPD	Programming under platform constraints and requirements (e.g., available development tools
SPD	Techniques for learning and mastering a platform-specific programming language
SPD	the constraints of mobile programming
SPD	the characteristics of scripting languages
SPD	the three-tier model of web programming
SPD	how the state is maintained in web programming
SPD	Web programming languages
SPD	Web platforms, frameworks, or meta-frameworks
SPD	Software as a Service
SPD	Web standards such as document object model, accessibility
SPD	Security and Privacy Considerations
SPD	Analyzing requirements for web applications
SPD	Computing services
SPD	Data management
SPD	Architecture
SPD	Storage solutions
SPD	and implement a web-based application using a microservice architecture design
SPD	the constraints, such as hosting, services, and scalability, related to web platforms
SPD	and contrast web programming with general-purpose programming
SPD	the differences between Software-as-a-Service and traditional software products
SPD	how web standards impact software development
SPD	an existing web application against current web standards
SPD	Development with
SPD	Mobile platform constraints
SPD	Access
SPD	Development
SPD	Mobile computing affordances
SPD	Specification and testing
SPD	Asynchronous computing
SPD	mobile programming with general-purpose programming
SPD	a location-aware mobile application with data API integration
SPD	a sensor-driven mobile application capable of logging data on a remote server
SPD	a communication app incorporating telephony and instant messaging
SPD	the pros and cons of native and cross-platform mobile application development
SPD	Types of robotic platforms and devices
SPD	Sensors, embedded computation, and effectors
SPD	Robot-specific languages and libraries
SPD	Robotic software architecture)
SPD	Robotic platform constraints and design considerations
SPD	Interconnections with physical or simulated systems
SPD	Robotic Algorithms
SPD	Safety and interaction considerations
SPD	and implement an application on a given robotic platform
SPD	Integrate an Arduino-based robot kit and program it to navigate a maze
SPD	robot-specific languages and techniques with those used for general-purpose software
SPD	the constraints a given robotic platform imposes on developers
SPD	Introduction to the unique characteristics of embedded systems
SPD	API for custom architectures
SPD	Embedded Systems
SPD	Embedded programming
SPD	Hard real-time systems vs soft real-time systems
SPD	Real-time resource management
SPD	Memory management
SPD	Safety considerations and safety analysis
SPD	Sensors and actuators
SPD	Analysis and verification
SPD	Application design
SPD	and implement a small embedded system for a given platform (e.g., a smart alarm clock or a
SPD	the unique characteristics of embedded systems versus other systems
SPD	Interface with sensors/actuators
SPD	Debug a problem with an existing embedded platform
SPD	different types of embedded architectures
SPD	which architecture is best for a given set of requirements
SPD	and develop software to interact with and control hardware
SPD	methods for real-time systems
SPD	real-time scheduling and schedulability analysis
SPD	formal specification and verification of timing constraints and properties
SPD	Historical and contemporary platforms for games
SPD	Real-time Simulation and Rendering Systems
SPD	Game Development Tools and Techniques
SPD	Game Engines
SPD	Game Design
SPD	Recall the characteristics of common general-purpose graphics processing architectures
SPD	the key stages of the immediate-mode rendering pipeline
SPD	the key constraints a specific game platform will likely impose on developers
SPD	how eSports are streamed to large audiences over the internet
SPD	complex mathematical functions into performant source code
SPD	an industry-standard graphics API to render a 3D model in a virtual scene
SPD	Modify a shader to change a visual effect according to stated requirements
SPD	a game for a particular platform according to the specification
SPD	Optimize a function for processing collision detection in a simulated environment
SPD	Assess a game's run-time and memory performance using an industry-standard tool and
SPD	the interfaces of different game platforms, highlighting their respective implications for
SPD	the key challenges in making a digital game that is cross-platform compatible
SPD	Express how game developers can enhance the accessibility of a game interface
SPD	novel forms of gameplay using frontier game platforms
SPD	Data Analysis Platforms
SPD	Prompt programming
SPD	Quantum Platforms
SPD	large datasets interactively
SPD	a backing track for a musical performance, such as live coding
SPD	compelling computational notebooks that construct a narrative for a given journalistic
SPD	interactive code that uses a dataset and generates exploratory graphics
SPD	a program that performs a task using LLM systems
SPD	Contrast a program developed by an AI platform and by a human
SPD	a system that interacts with a human without using a screen
SPD	a program using a notebook computing platform (e.g., searching, sorting, or graph
SPD	a quantum gate outcome using a quantum platform
SPD	Privacy and data protection
SPD	Accessibility in mobile design
SPD	Security and cybersecurity
SPD	Social impacts of mobile technology
SPD	Ethical use of AI and algorithms
SPD	mobile applications with accessibility in mind, ensuring effective use by people with
SPD	proficiency in secure coding practices to mitigate risks associated with various security
SPD	the broader social impacts of mobile technology, including its influence on communication
SPD	Privacy concerns with mobile apps
SPD	Designing for inclusivity and accessibility
SPD	Ethical use of AI in mobile apps
SPD	Sustainable app development and server hosting
SPD	Avoiding spam or intrusive notifications
SPD	Addressing cyberbullying and harassment
SPD	Promoting positive online communities
SPD	Monetization and advertising
SPD	Ethical use of gamification
SPD	Understand how mobile computing impacts communications and the flow of information within
SPD	mobile apps that have made daily tasks easier/faster
SPD	how the ubiquity of mobile computing has affected work-life balance
SPD	Understand how mobile computing impacts health monitoring and healthcare services
SPD	how mobile apps are used to educate about and help achieve UN sustainability goals
SPD	Intellectual Property Rights in Creative Industries
SPD	Fair Access to Play
SPD	Game-Related Health and Safety
SPD	Platform Hardware Supply Chain and Sustainability
SPD	Representation in the Media and Industry
SPD	how creators can protect their intellectual property
SPD	common pitfalls in game interfaces that exclude players with impaired or non-functional
SPD	how heuristic evaluation can be used to identify usability problems in game interfaces
SPD	why upper body injuries are common in eSports
SPD	how to reform characters and dialogues in a scene to reduce stereotype threat
SPD	Modify a policy for a LAN party event to include mitigations that lower the risk of fire
SPD	a gamification strategy to motivate serious play for an awareness-raising game
SPD	the role of company hiring policies and advocacy on social mobility
SPD	Assess the appropriateness of two manufacturers for producing a new game console
SPD	options for open-source licensing of a game development tool
SPD	whether games are addictive
SPD	a video game that successfully advocates for climate science
SPD	Fairness, transparency, and accountability in robotic algorithms
SPD	Mitigating biases in robot decision-making
SPD	Public safety in shared spaces with robots
SPD	Compliance with data protection laws
SPD	Patient consent and trust in medical robots
SPD	instances of bias in robotic algorithms and propose strategies to mitigate them
SPD	and critique robotic systems for ethical and fairness considerations, suggesting
SPD	real-world examples of biases in robot decision-making and develop strategies to reduce
SPD	the impact of patient consent and trust on the effectiveness of medical robot deployments
SPD	Ethical guidelines when using AI models to assist in journalism and content creation
SPD	Accountability for AI-generated outputs
SPD	Behavior among prompt programmers and AI developers
SPD	Trust with the public when using AI models
SPD	ethical codes of conduct and professional standards relevant to prompt programming and
SPD	communication plans and materials to educate the public about AI capabilities, limitations
SPD	Memory
SPD	Data Stores
SPD	One or more of the following properties and Explain, KA 6
SPD	Atomicity
SPD	The overfitting problem / controlling solution
SPD	Working with Data
SPD	Representations
SPD	Machine learning evaluation
SPD	Basic neural networks
SPD	Ethics for Machine Learning Explain
SPD	Real-time Simulation and Rendering Systems
SPD	Game Development Tools and Techniques:
SPD	Game Engines
SPD	Game Design
SPD	Taylor series
SPD	Multivariate calculus  partial derivatives, gradient
SPD	Optimization  convexity, global vs local minima
SPD	ODEs  definition, Euler method, applications to
SPD	CS applications  gradient descent for machine
SPD	CS I
SPD	CS II
SPD	Mathematical and Statistical Foundations
SPD	Algorithms
SPD	Introduction to Computing Systems
SPD	Programming Language Concepts
SPD	Introduction to Computing Applications
SPD	Capstone
SPD	Data Structures and Algorithms
SPD	Programming Languages
SPD	Software Engineering
SPD	One Systems elective:
SPD	One elective from Applications:
SPD	Two from Systems electives:
SPD	Two electives from Applications:
SPD	Theory of Computation
SPD	Operating Systems
SPD	Computer Architecture
SPD	Parallel and Distributed Computing
SPD	Networking
SPD	Pick one of:
SPD	Security
SPD	Two electives from:
SPD	Pick three of:
SPD	Society, Ethics, and the Profession
SPD	Three open CS electives
SPD	Society, Ethics, and the Profession course"""


def resolve(name: str) -> Path:
    env_dir = os.environ.get("SKILLGAP_INPUT_DIR")
    candidates = []
    if env_dir:
        candidates.append(Path(env_dir) / name)
    for root in [Path("/kaggle/input/datasets/studyhub991/skill-gap-inputs-v1"),
                 Path("/kaggle/input/skill-gap-inputs-v1/bundle"),
                 Path("/kaggle/input/skill-gap-inputs-v1")]:
        candidates.append(root / name)
    repo = Path(__file__).resolve().parents[2] / "datasets"
    mapping = {
        "hf_job_skill_set.csv": repo / "hf_job_skill_set.csv",
    }
    if name in mapping:
        candidates.append(mapping[name])
    for c in candidates:
        if c.exists():
            return c
    raise FileNotFoundError(f"{name} not found; tried {candidates}")


def main() -> None:
    t0 = time.time()
    out_dir = Path(os.environ.get("SKILLGAP_OUTPUT_DIR", "/kaggle/working"))
    out_dir.mkdir(parents=True, exist_ok=True)

    topics = []
    for line in CS2023_TOPICS.strip().splitlines():
        ka, topic = line.split("\t", 1)
        topics.append((ka, topic.strip()))
    assert len(topics) >= 2000, f"topic list too small: {len(topics)}"
    kas = sorted({ka for ka, _ in topics})
    assert len(kas) == 17, f"expected 17 KAs, got {len(kas)}"

    acad_counts = Counter()
    for s in pd.read_csv(resolve("hf_job_skill_set.csv"),
                         usecols=["job_skill_set"])["job_skill_set"].dropna():
        skills_str = str(s).strip().strip("[]").replace("'", "")
        for skill in skills_str.split(","):
            skill = skill.strip().lower()
            if skill:
                acad_counts[skill] += 1
    academic_top = [s for s, _ in acad_counts.most_common(PROFILE_N)]
    academic_set = set(academic_top)

    import torch
    from sentence_transformers import SentenceTransformer
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = SentenceTransformer(MODEL_NAME, device=device)
    topic_texts = [t for _, t in topics]
    emb_t = model.encode(topic_texts, device=device, convert_to_numpy=True)
    emb_a = model.encode(academic_top, device=device, convert_to_numpy=True)

    sim = cosine_similarity(emb_t, emb_a)
    max_sims = sim.max(axis=1)
    best_idx = sim.argmax(axis=1)

    # reverse: academic top-500 vs topics
    max_sims_rev = sim.max(axis=0)

    matches_df = pd.DataFrame({
        "ka_code": [ka for ka, _ in topics],
        "cs2023_topic": topic_texts,
        "best_academic_match": [academic_top[i] for i in best_idx],
        "cosine_similarity": np.round(max_sims, 4),
        "lexically_exact": [int(t.lower() in academic_set) for t in topic_texts],
    })

    ka_arr = np.array([ka for ka, _ in topics])
    rng = np.random.RandomState(SEED)
    per_ka_rows = []
    for ka in kas:
        mask = ka_arr == ka
        n = int(mask.sum())
        sims_k = max_sims[mask]
        lex_k = matches_df.loc[mask, "lexically_exact"].values
        row = {
            "ka_code": ka,
            "n_topics": n,
            "coverage_lexical": round(float(lex_k.mean()), 4),
        }
        for tau in TAUS:
            cov = sims_k >= tau
            point = float(cov.mean())
            b = [float(np.mean(rng.choice(cov, size=n, replace=True)))
                 for _ in range(BOOTSTRAP_N)]
            lo, hi = np.percentile(b, [2.5, 97.5])
            row[f"coverage_sem_tau_{tau}"] = round(point, 4)
            row[f"ci_lo_tau_{tau}"] = round(float(lo), 4)
            row[f"ci_hi_tau_{tau}"] = round(float(hi), 4)
        per_ka_rows.append(row)
    per_ka_df = pd.DataFrame(per_ka_rows)

    rng2 = np.random.RandomState(SEED)
    sens_rows = []
    for tau in TAUS:
        cov = max_sims >= tau
        point = float(cov.mean())
        b = [float(np.mean(rng2.choice(cov, size=len(cov), replace=True)))
             for _ in range(BOOTSTRAP_N)]
        lo, hi = np.percentile(b, [2.5, 97.5])
        rev = float((max_sims_rev >= tau).mean())
        sens_rows.append({
            "tau": tau,
            "overall_coverage_semantic": round(point, 4),
            "CI_Lower": round(float(lo), 4),
            "CI_Upper": round(float(hi), 4),
            "reverse_coverage_academic_top500": round(rev, 4),
        })
    sens_df = pd.DataFrame(sens_rows)

    rev05 = float((max_sims_rev >= TAU).mean())
    metrics = {
        "experiment_id": "CURR01_cs2023_anchor",
        "status": "completed",
        "runtime_sec": round(time.time() - t0, 2),
        "seed": SEED,
        "bootstrap_n": BOOTSTRAP_N,
        "model": MODEL_NAME,
        "device": device,
        "n_kas": len(kas),
        "n_topics": len(topics),
        "overall_coverage_sem_tau_0.5": sens_df.loc[sens_df.tau == TAU,
                                                    "overall_coverage_semantic"].iloc[0],
        "reverse_coverage_academic_tau_0.5": round(rev05, 4),
        "per_ka": per_ka_rows,
        "sensitivity": sens_rows,
    }
    per_ka_df.to_csv(out_dir / "table_cs2023_per_ka.csv", index=False)
    sens_df.to_csv(out_dir / "table_cs2023_sensitivity.csv", index=False)
    matches_df.to_csv(out_dir / "cs2023_topic_matches.csv", index=False)
    with open(out_dir / "metrics.json", "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
    print(json.dumps(metrics, indent=2)[:4000])


if __name__ == "__main__":
    sys.exit(main())
