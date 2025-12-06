import os
import unittest

from main import EnvDefaults, load_env_defaults, parse_args


class TestEnvLoading(unittest.TestCase):
    """Validate that environment defaults are loaded and overridable via CLI."""

    def setUp(self) -> None:
        self._env_backup = os.environ.copy()

    def tearDown(self) -> None:
        os.environ.clear()
        os.environ.update(self._env_backup)

    def test_env_defaults_are_applied(self) -> None:
        os.environ["DB_USER"] = "env_user"
        os.environ["DB_PASSWORD"] = "env_pw"
        os.environ["DB_HOSTS"] = "1.1.1.1,2.2.2.2"
        os.environ["DB_PORT"] = "4000"

        env_defaults: EnvDefaults = load_env_defaults()
        self.assertEqual(env_defaults.user, "env_user")
        self.assertEqual(env_defaults.password, "env_pw")
        self.assertEqual(env_defaults.hosts, "1.1.1.1,2.2.2.2")
        self.assertEqual(env_defaults.port, 4000)

        args = parse_args(env_defaults, argv=[])
        self.assertEqual(args.user, "env_user")
        self.assertEqual(args.password, "env_pw")
        self.assertEqual(args.hosts, "1.1.1.1,2.2.2.2")
        self.assertEqual(args.port, 4000)

    def test_cli_overrides_env_defaults(self) -> None:
        os.environ["DB_USER"] = "env_user"
        os.environ["DB_PASSWORD"] = "env_pw"
        os.environ["DB_HOSTS"] = "1.1.1.1,2.2.2.2"
        os.environ["DB_PORT"] = "4000"

        env_defaults: EnvDefaults = load_env_defaults()
        args = parse_args(
            env_defaults,
            argv=[
                "--user",
                "cli_user",
                "--password",
                "cli_pw",
                "--hosts",
                "3.3.3.3",
                "--port",
                "5000",
            ],
        )

        self.assertEqual(args.user, "cli_user")
        self.assertEqual(args.password, "cli_pw")
        self.assertEqual(args.hosts, "3.3.3.3")
        self.assertEqual(args.port, 5000)


if __name__ == "__main__":
    unittest.main()


