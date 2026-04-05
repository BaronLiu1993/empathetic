import numpy as np
import pytest
from unittest.mock import patch, AsyncMock


class TestProcessBrainAnalysis:
    @patch("service.brain_analysis.insert_data_to_db", new_callable=AsyncMock, return_value=["id1"])
    @patch("service.brain_analysis.predict_from_html")
    def test_calls_save_brain_analysis(self, mock_predict, mock_insert):
        import asyncio
        from service.brain_analysis import save_brain_analysis_results

        mock_predict.return_value = (np.zeros((2, 10)), ["s1", "s2"])

        asyncio.run(save_brain_analysis_results("<p>test</p>", "user1"))

        mock_predict.assert_called_once_with("<p>test</p>")
        mock_insert.assert_called_once()

    @patch("service.brain_analysis.insert_data_to_db", new_callable=AsyncMock)
    @patch("service.brain_analysis.predict_from_html", side_effect=RuntimeError("model error"))
    def test_raises_on_failure(self, mock_predict, mock_insert):
        import asyncio
        from service.brain_analysis import save_brain_analysis_results

        with pytest.raises(RuntimeError, match="model error"):
            asyncio.run(save_brain_analysis_results("<p>test</p>", "user1"))

        mock_predict.assert_called_once()
        mock_insert.assert_not_called()
