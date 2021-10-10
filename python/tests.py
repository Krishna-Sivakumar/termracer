import main
from RaceClient import RaceClient, BACKSPACE, CTRLC
from random import randint
import unittest


class TestRaceClient(unittest.TestCase):

    passage = "this is a test passage."

    def testBasic(self):
        # Instantiate a client and type in only correct characters
        client = RaceClient(self.passage)
        for char in self.passage:
            client.typeCharacter(char)

        assert client.isOver()
        assert client.statistics()["accuracy"] == 100
        assert client.total == len(self.passage)

        return client

    def testErrorsAndAccuracy(self):
        client = RaceClient(self.passage)
        passage_length = len(self.passage)
        total_errors, total = 0, 0

        for pointer, char in enumerate(self.passage):
            client.typeCharacter(char)
            total += 1

            random_errors = min(randint(0, 5), passage_length-pointer-1)

            for _ in range(random_errors):
                # Type a random number of wrong characters
                client.typeCharacter("⠁")
                # Delete a character everytime you type it
                client.typeCharacter(BACKSPACE)
                total_errors += 1
                total += 1

        assert client.isOver()

        statistics_dict = client.statistics()

        # Check if the total errors match the test module's values
        assert statistics_dict["total_errors"] == total_errors
        assert statistics_dict["total_characters_typed"] == total
        assert statistics_dict["accuracy"] == int(
            ((total-total_errors)/total)*100
        )

    def testWriteAndRead(self):
        import os.path
        from subprocess import run

        client = self.testBasic()

        main.temp_file_path = "test_tmp_file.dat"

        # Path to test_tmp_file.dat
        file_path = os.path.join(main.script_path, main.temp_file_path)

        # Write to the file 1->10 times
        random_writes = randint(1, 10)
        for _ in range(random_writes):
            main.writeResultsToFile(client)

        # Check if the file exists
        assert os.path.exists(file_path)

        lines = main.getRacesFromFile(main.temp_file_path)

        # Check if the correct number of lines were written
        assert len(lines) == random_writes

        # Remove test file
        run(["rm", file_path])

    def testExit(self):
        client = RaceClient(self.passage)

        # Checks if the client exits
        assert client.typeCharacter(CTRLC)

    def testPassages(self):
        import os.path
        try:
            assert os.path.exists(os.path.join(
                main.script_path, "passages.txt"))
        except AssertionError:
            raise AssertionError(
                "passages.txt must exist at the file directory")


if __name__ == "__main__":
    unittest.main()
