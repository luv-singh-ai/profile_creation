import unittest
from unittest.mock import patch
from ai import process_vOTP

class TestProcessVOTP(unittest.TestCase):
    @patch("utils.profile.verify_otp")
    @patch("utils.openai_utils.get_run_status")
    @patch("utils.openai_utils.get_assistant_message")
    @patch("utils.openai_utils.upload_message")
    def test_process_vOTP_success(self, mock_upload_message, mock_get_assistant_message, mock_get_run_status, mock_verify_otp):
        # Mock the necessary functions and return values
        mock_verify_otp.return_value = True
        mock_upload_message.return_value = "run_id", "completed"
        mock_get_run_status.return_value = "completed"
        mock_get_assistant_message.return_value = "OTP verified successfully."

        # Define the input parameters
        parameters = {"OTP": "123456"}
        tool_id = "tool_id"
        thread_id = "thread_id"
        run_id = "run_id"

        # Call the function to be tested
        assistant_message, history = process_vOTP(parameters, tool_id, thread_id, run_id)

        # Assert the expected results
        self.assertEqual(assistant_message, "OTP verified successfully.")
        self.assertEqual(history, {
            "thread_id": thread_id,
            "run_id": run_id,
            "status": "completed"
        })

    @patch("utils.profile.verify_otp")
    @patch("utils.openai_utils.get_run_status")
    @patch("utils.openai_utils.get_assistant_message")
    @patch("utils.openai_utils.upload_message")
    def test_process_vOTP_failure(self, mock_upload_message, mock_get_assistant_message, mock_get_run_status, mock_verify_otp):
        # Mock the necessary functions and return values
        mock_verify_otp.return_value = False
        mock_upload_message.return_value = "run_id", "completed"
        mock_get_run_status.return_value = "completed"
        mock_get_assistant_message.return_value = "OTP verification failed."

        # Define the input parameters
        parameters = {"OTP": "123456"}
        tool_id = "tool_id"
        thread_id = "thread_id"
        run_id = "run_id"

        # Call the function to be tested
        assistant_message, history = process_vOTP(parameters, tool_id, thread_id, run_id)

        # Assert the expected results
        self.assertEqual(assistant_message, "OTP verification failed.")
        self.assertEqual(history, {
            "thread_id": thread_id,
            "run_id": run_id,
            "status": "failed"
        })

if __name__ == "__main__":
    unittest.main()