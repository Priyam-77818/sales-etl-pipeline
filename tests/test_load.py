"""
Tests – Load Layer
Covers: PostgreSQL connection failure, S3 credential failure.
Uses mocking so no real DB or AWS credentials are required.
"""

import pytest
import pandas as pd
from unittest.mock import MagicMock, patch

from load.postgres_loader import load_dataframe, check_connection


class TestPostgresLoader:

    def test_check_connection_returns_false_on_failure(self):
        """check_connection returns False when DB is unreachable."""
        engine = MagicMock()
        engine.connect.side_effect = Exception("Connection refused")
        result = check_connection(engine)
        assert result is False

    def test_check_connection_returns_true_on_success(self):
        """check_connection returns True on a healthy connection."""
        engine = MagicMock()
        conn = MagicMock()
        engine.connect.return_value.__enter__ = MagicMock(return_value=conn)
        engine.connect.return_value.__exit__ = MagicMock(return_value=False)
        result = check_connection(engine)
        assert result is True

    def test_load_dataframe_raises_on_engine_error(self):
        """load_dataframe propagates exceptions from SQLAlchemy."""
        df = pd.DataFrame({"a": [1, 2]})
        engine = MagicMock()

        with patch("pandas.DataFrame.to_sql", side_effect=Exception("DB error")):
            with pytest.raises(Exception, match="DB error"):
                load_dataframe(df, "test_table", engine)

    def test_load_dataframe_calls_to_sql(self):
        """load_dataframe calls DataFrame.to_sql with correct parameters."""
        df = pd.DataFrame({"col1": [1, 2], "col2": ["a", "b"]})
        engine = MagicMock()

        with patch.object(df, "to_sql") as mock_to_sql:
            load_dataframe(df, "test_table", engine, if_exists="append")
            mock_to_sql.assert_called_once()
            call_kwargs = mock_to_sql.call_args.kwargs
            assert call_kwargs["name"] == "test_table"
            assert call_kwargs["if_exists"] == "append"


class TestS3Backup:

    def test_backup_handles_missing_credentials(self):
        """backup_all logs error and returns failed count when credentials missing."""
        from load.s3_backup import backup_all
        from botocore.exceptions import NoCredentialsError

        with patch("boto3.client") as mock_client:
            mock_s3 = MagicMock()
            mock_s3.upload_file.side_effect = NoCredentialsError()
            mock_client.return_value = mock_s3

            # Should not raise — returns dict with failed count
            result = backup_all(bucket="test-bucket")
            assert "uploaded" in result
            assert "failed" in result

    def test_upload_file_returns_false_on_error(self):
        """upload_file returns False when upload fails."""
        from load.s3_backup import upload_file
        from botocore.exceptions import ClientError

        mock_s3 = MagicMock()
        mock_s3.upload_file.side_effect = ClientError(
            {"Error": {"Code": "403", "Message": "Forbidden"}}, "PutObject"
        )
        result = upload_file(mock_s3, "/fake/path.csv", "my-bucket", "cleaned/path.csv")
        assert result is False
