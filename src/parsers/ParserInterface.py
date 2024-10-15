from typing import Optional
from src.Sample import Sample


class Parser:
    """An abstract base class used to define the interface of a parser"""

    def getNextFrame(self) -> Optional[Sample]:
        raise NotImplementedError
