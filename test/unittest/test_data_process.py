import random
import unittest
from unittest.mock import Mock

from model.model import Pair, PairList
from src.data_process import create_pair_from_list


class TestCreatePairFromList(unittest.TestCase):
    def setUp(self):
        # Create mock discord.User objects
        self.users = []
        for i in range(5):
            user = Mock()
            user.display_name = f"User{i}"
            user.avatar = Mock()
            user.avatar.url = f"http://avatar/{i}"
            self.users.append(user)

        # Create test groups
        self.groups = ["Group A", "Group B", "Group C", "Group D", "Group E"]

    def test_empty_users_raises_error(self):
        with self.assertRaises(ValueError):
            create_pair_from_list([], self.groups)

    def test_empty_groups_raises_error(self):
        with self.assertRaises(ValueError):
            create_pair_from_list(self.users, [])

    def test_both_empty_raises_error(self):
        with self.assertRaises(ValueError):
            create_pair_from_list([], [])

    def test_equal_length_lists(self):
        result = create_pair_from_list(self.users, self.groups)

        self.assertIsInstance(result, PairList)
        self.assertEqual(len(result.pairs), 5)

    def test_more_users_than_groups(self):
        extra_users = self.users + [Mock()]
        result = create_pair_from_list(extra_users, self.groups)

        self.assertEqual(len(result.pairs), 5)  # Should be limited by group count

    def test_more_groups_than_users(self):
        extra_groups = self.groups + ["Group F"]
        result = create_pair_from_list(self.users, extra_groups)

        self.assertEqual(len(result.pairs), 5)  # Should be limited by user count

    def test_all_elements_from_original_lists(self):
        result = create_pair_from_list(self.users, self.groups)

        for pair in result.pairs:
            self.assertIn(pair.user, self.users)
            self.assertIn(pair.choice, self.groups)

    def test_randomness(self):
        # Seed random for reproducibility in test
        random.seed(42)
        result1 = create_pair_from_list(self.users, self.groups)

        random.seed(43)  # Different seed
        result2 = create_pair_from_list(self.users, self.groups)

        # Check if at least one pair is different
        at_least_one_different = False
        for i in range(len(result1.pairs)):
            if (
                result1.pairs[i].user != result2.pairs[i].user
                or result1.pairs[i].choice != result2.pairs[i].choice
            ):
                at_least_one_different = True
                break

        self.assertTrue(at_least_one_different)

    def test_pair_structure(self):
        result = create_pair_from_list(self.users, self.groups)

        for pair in result.pairs:
            self.assertIsInstance(pair, Pair)
            self.assertTrue(hasattr(pair, "user"))
            self.assertTrue(hasattr(pair, "choice"))


if __name__ == "__main__":
    unittest.main()
