import logging
import os
import tempfile
import unittest

from utils.logging import configure_logging, get_logger


class LoggingConfigurationTests(unittest.TestCase):
    def test_configure_logging_writes_to_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = os.path.join(temp_dir, "bot.log")
            os.environ["LOG_FILE"] = log_path

            root_logger = logging.getLogger()
            for handler in list(root_logger.handlers):
                root_logger.removeHandler(handler)
                handler.close()

            configure_logging()
            logger = get_logger("test.logging")
            logger.info("hello from logging test")

            for handler in root_logger.handlers:
                handler.flush()

            self.assertTrue(os.path.exists(log_path))
            with open(log_path, encoding="utf-8") as log_file:
                self.assertIn("hello from logging test", log_file.read())

    def test_configure_logging_sets_third_party_loggers_to_info(self) -> None:
        root_logger = logging.getLogger()
        for handler in list(root_logger.handlers):
            root_logger.removeHandler(handler)
            handler.close()

        configure_logging()

        self.assertEqual(logging.getLogger("msrest.universal_http").level, logging.INFO)
        self.assertEqual(logging.getLogger("urllib3.connectionpool").level, logging.INFO)
        self.assertEqual(logging.getLogger("aiohttp.access").level, logging.INFO)


if __name__ == "__main__":
    unittest.main()
