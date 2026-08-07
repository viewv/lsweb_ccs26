import unittest

import numpy as np

from adaptive_sampling import (
    approximate_normal_half_width,
    choose_stopping_stage,
    issue_truth_from_joint_counts,
    planned_stages,
    simulate_nested_counts,
)


class AdaptiveSamplingTests(unittest.TestCase):
    def test_planned_stages_for_top500k(self):
        np.testing.assert_array_equal(
            planned_stages(500_000),
            np.array([10_000, 20_000, 40_000, 80_000, 160_000, 320_000, 500_000]),
        )

    def test_planned_stages_for_top100k_impact_frame(self):
        np.testing.assert_array_equal(
            planned_stages(100_000),
            np.array([2_000, 4_000, 8_000, 16_000, 32_000, 64_000, 100_000]),
        )

    def test_commoncrawl_stages_double_and_end_at_population(self):
        np.testing.assert_array_equal(
            planned_stages(24_834_442),
            np.array(
                [496_689, 993_378, 1_986_756, 3_973_512, 7_947_024,
                 15_894_048, 24_834_442]
            ),
        )

    def test_normal_interval_example_with_fpc(self):
        counts = np.array([[[53]]], dtype=np.int64)
        stages = np.array([10_000], dtype=np.int64)
        half_width = approximate_normal_half_width(counts, stages, 500_000)
        self.assertAlmostEqual(float(half_width[0, 0, 0]), 0.001408813606)
        estimate = 53 / 10_000
        self.assertAlmostEqual(estimate - half_width[0, 0, 0], 0.003891186394)
        self.assertAlmostEqual(estimate + half_width[0, 0, 0], 0.006708813606)

    def test_adaptive_rule_never_stops_at_pilot(self):
        shape = (2, 3, 1)
        statistics = {
            "estimates": np.full(shape, 0.10),
            "relative_change": np.zeros(shape),
            "relative_margin": np.zeros(shape),
        }
        positive_counts = np.ones(shape, dtype=np.int64)
        stop = choose_stopping_stage(
            "adaptive", statistics, positive_counts, 0.10
        )
        self.assertTrue(np.all(stop == 1))

    def test_adaptive_rule_requires_change_and_margin_conditions(self):
        shape = (1, 4, 1)
        statistics = {
            "estimates": np.full(shape, 0.01),
            "relative_change": np.array([[[np.inf], [0.05], [0.05], [0.05]]]),
            "relative_margin": np.array([[[np.inf], [0.20], [0.08], [0.00]]]),
        }
        positive_counts = np.ones(shape, dtype=np.int64)
        stop = choose_stopping_stage(
            "adaptive", statistics, positive_counts, 0.10
        )
        self.assertEqual(int(stop[0, 0]), 2)

    def test_zero_positive_case_cannot_stop_before_census(self):
        shape = (1, 4, 1)
        statistics = {
            "estimates": np.zeros(shape),
            "relative_change": np.zeros(shape),
            "relative_margin": np.zeros(shape),
        }
        positive_counts = np.zeros(shape, dtype=np.int64)
        stop = choose_stopping_stage(
            "adaptive", statistics, positive_counts, 0.10
        )
        self.assertEqual(int(stop[0, 0]), 3)

    def test_nested_simulation_reaches_exact_census_truth(self):
        joint_counts = np.array([50, 10, 20, 5, 7, 3, 4, 1], dtype=np.int64)
        stages = planned_stages(int(joint_counts.sum()))
        sampled = simulate_nested_counts(joint_counts, stages, trials=5, seed=7)
        truth = issue_truth_from_joint_counts(joint_counts)
        expected = np.broadcast_to(truth, (sampled.shape[0], truth.size))
        np.testing.assert_allclose(sampled[:, -1, :] / joint_counts.sum(), expected)


if __name__ == "__main__":
    unittest.main()
