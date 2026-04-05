import numpy as np
import pytest
from unittest.mock import patch, MagicMock, AsyncMock


class TestPredictFromHtml:
    @patch("service.brain_analysis.shutil.rmtree")
    @patch("service.brain_analysis.clean_text", return_value="cleaned text")
    @patch("service.brain_analysis._get_model")
    def test_returns_preds_and_segments(self, mock_get_model, mock_clean, mock_rmtree):
        mock_model = MagicMock()
        mock_model.get_events_dataframe.return_value = MagicMock()
        mock_model.predict.return_value = (np.zeros((3, 20484)), ["seg1", "seg2", "seg3"])
        mock_get_model.return_value = mock_model

        from service.brain_analysis import predict_from_html

        preds, segments = predict_from_html("<p>hello</p>")

        mock_clean.assert_called_once_with("<p>hello</p>")
        mock_model.get_events_dataframe.assert_called_once()
        mock_model.predict.assert_called_once()
        assert preds.shape == (3, 20484)
        assert len(segments) == 3

    @patch("service.brain_analysis.shutil.rmtree")
    @patch("service.brain_analysis.clean_text", return_value="cleaned text")
    @patch("service.brain_analysis._get_model")
    def test_cleans_up_tmpdir_on_success(self, mock_get_model, mock_clean, mock_rmtree):
        mock_model = MagicMock()
        mock_model.predict.return_value = (np.zeros((1, 10)), ["seg"])
        mock_get_model.return_value = mock_model

        from service.brain_analysis import predict_from_html

        predict_from_html("<p>test</p>")

        mock_rmtree.assert_called_once()
        assert mock_model.cache_folder == "./cache"

    @patch("service.brain_analysis.shutil.rmtree")
    @patch("service.brain_analysis.clean_text", return_value="cleaned text")
    @patch("service.brain_analysis._get_model")
    def test_cleans_up_tmpdir_on_failure(self, mock_get_model, mock_clean, mock_rmtree):
        mock_model = MagicMock()
        mock_model.predict.side_effect = RuntimeError("inference failed")
        mock_get_model.return_value = mock_model

        from service.brain_analysis import predict_from_html

        with pytest.raises(RuntimeError, match="inference failed"):
            predict_from_html("<p>test</p>")

        mock_rmtree.assert_called_once()
        assert mock_model.cache_folder == "./cache"

    @patch("service.brain_analysis.shutil.rmtree")
    @patch("service.brain_analysis.clean_text", return_value="cleaned text")
    @patch("service.brain_analysis._get_model")
    def test_sets_cache_folder_to_tmpdir(self, mock_get_model, mock_clean, mock_rmtree):
        cache_folders = []
        mock_model = MagicMock()

        def capture_cache(*args, **kwargs):
            cache_folders.append(mock_model.cache_folder)
            return MagicMock()

        mock_model.get_events_dataframe.side_effect = capture_cache
        mock_model.predict.return_value = (np.zeros((1, 10)), ["seg"])
        mock_get_model.return_value = mock_model

        from service.brain_analysis import predict_from_html

        predict_from_html("<p>test</p>")

        # cache_folder was set to a tmpdir during inference, not ./cache
        assert len(cache_folders) == 1
        assert cache_folders[0] != "./cache"


class TestInsertDataToDb:
    @pytest.mark.asyncio
    @patch("service.brain_analysis.get_mongo_write_client")
    async def test_inserts_correct_docs(self, mock_get_client):
        mock_collection = AsyncMock()
        mock_collection.insert_many.return_value = MagicMock(inserted_ids=["id1", "id2"])
        mock_db = MagicMock()
        mock_db.__getitem__ = MagicMock(return_value=mock_collection)
        mock_client = MagicMock()
        mock_client.__getitem__ = MagicMock(return_value=mock_db)
        mock_get_client.return_value = mock_client

        from service.brain_analysis import insert_data_to_db

        seg1 = MagicMock(start=0.0, duration=1.0)
        seg2 = MagicMock(start=1.0, duration=1.0)
        preds = np.array([[0.1, 0.2], [0.3, 0.4]])

        result = await insert_data_to_db(preds, [seg1, seg2], "test_source", "user1")

        mock_collection.insert_many.assert_called_once()
        docs = mock_collection.insert_many.call_args[0][0]
        assert len(docs) == 2
        assert docs[0]["user_id"] == "user1"
        assert docs[0]["source"] == "test_source"
        assert docs[0]["timepoint"] == 0.0
        assert docs[0]["activations"] == [0.1, 0.2]
        assert result == ["id1", "id2"]


class TestSaveBrainAnalysisResults:
    @pytest.mark.asyncio
    @patch("service.brain_analysis.insert_data_to_db", new_callable=AsyncMock)
    @patch("service.brain_analysis.predict_from_html")
    async def test_text_pipeline(self, mock_predict, mock_insert):
        mock_predict.return_value = (np.zeros((2, 10)), ["s1", "s2"])
        mock_insert.return_value = ["id1", "id2"]

        from service.brain_analysis import save_brain_analysis_results

        preds, segments = await save_brain_analysis_results("<p>hello</p>", "user1")

        mock_predict.assert_called_once_with("<p>hello</p>")
        mock_insert.assert_called_once()
        assert preds.shape == (2, 10)
        assert len(segments) == 2
