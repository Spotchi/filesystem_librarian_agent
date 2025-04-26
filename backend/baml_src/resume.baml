// Defining a data model.
class Suggestion {
  structure string
  explanation string
}

class FileOperations {
  operations FileOperation[]
}

class FileOperation {
  operationType string
  sourcePath string
  destinationPath string
  isDirectory bool
  description string
}

// Create a function to extract the resume from a string.
function SuggestFileOperations(resume: string) -> Suggestion {
  // Specify a client as provider/model-name
  // you can use custom LLM params with a custom client name from clients.baml like "client CustomHaiku"
  client "openai/gpt-4o" // Set OPENAI_API_KEY to use this client.
  prompt #"
You are an expert knowledge management assistant specializing in organizing directories and files on a personal computer.

You will be given a folder structure .
To solve the task, you must propose a reorganisation of the files and folders using one or more of the following guidelines:
- All files must be contained in a folder
- Folders should be named consistently and clearly, and be consistent with the names of the files they contain
- Reduce duplicates in the hierarchy

Here are a few examples of how to use these guidelines:
---
Structure:
.
├── AI
│   └── Reinforcement learning
└── Agent.md

Suggested structure:
.
├── AI
│  ├── Reinforcement learning
│  └ Agent.md
└── Cooking

Explanation:
- All files must be contained in a folder : I moved `Agent.md` into the `AI` folder since it is related to AI not related to Cooking.

---
Structure:
.
├── AI
│   └── Deep learning
│       ├── gradient descent.md
│       └── vegetable masala.md
└── Cooking
    └── stainless steel pans.md

Suggested structure:
.
├── AI
│   └── Deep learning
│       └── gradient descent.md
└── Cooking
    ├── stainless steel pans.md
    └── vegetable masala.md

Explanation:
- Folders should be named consistently and clearly, and be consistent with the names of the files they contain: Since `vegetable masala` was not related to `AI` but was related to `Cooking`, I moved it to that folder. 

Translate the operations needed for this into a list of file operations and call the suggestion_tool if operations are needed. Also ask the user if they want to apply the operations.

    {{ resume }}

    {{ ctx.output_format }}
  "#
}

function DetermineFileOperations(original_structure: string, suggestion: Suggestion) -> FileOperations {
  client "openai/gpt-4o"
  prompt #"
    Based on the following suggestion of a reorganisation of a folder, determine the list of file operations needed to achieve the reorganisation.

    Original structure:
    {{ original_structure }}

    Suggested structure:
    {{ suggestion.structure }}

    {{ ctx.output_format }}
  "#
}

test reorg_example {
  functions [DetermineFileOperations]
  args {
    suggestion {
      structure #"
        ├── AI
        │   └── Deep learning
        │       └── gradient descent.md
        └── Cooking
            ├── stainless steel pans.md
            └── vegetable masala.md
      "#
      explanation "hello"
    }
    original_structure #"
      ├── AI
      │   └── Deep learning
      │       ├── gradient descent.md
      │       └── vegetable masala.md
      └── Cooking
        └── stainless steel pans.md
    "#
  }
}

// Test the function with a sample resume. Open the VSCode playground to run this.
test deep_learning_from_recipe {
  functions [SuggestFileOperations]
  args {
    resume #"
      Structure:
      .
      ├── AI
      │   └── Deep learning
      │       ├── gradient descent.md
      │       └── vegetable masala.md
      └── Cooking
          └── stainless steel pans.md
    "#
  }
}
