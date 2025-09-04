from dataclasses import dataclass, field
from typing import Any, Dict, List


# INCORRECT WAY - DO NOT DO THIS
@dataclass
class BadExample:
    id: int
    items: List[str] = field(default_factory=list) # This list is shared!

b1 = BadExample(id=1)
b2 = BadExample(id=2)

# Modify the list for the first instance
b1.items.append("apple")

print(f"b1 items: {b1.items}")
print(f"b2 items: {b2.items}") # Oh no, b2 was also changed!

# --- Console Output ---
# b1 items: ['apple']
# b2 items: ['apple']