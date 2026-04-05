import sys
from unittest.mock import MagicMock

# Mock tribev2 before any test module imports it
mock_tribev2 = MagicMock()
sys.modules["tribev2"] = mock_tribev2
sys.modules["tribev2.tribev2"] = mock_tribev2
