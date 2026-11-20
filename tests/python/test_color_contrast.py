import unittest

from support import RepoTestCase, load_script, requires_git, run_json, run_script

SCRIPT = "accessibility-audit-ios/scripts/color_contrast.py"
cc = load_script(SCRIPT)

WHITE, BLACK = (1.0, 1.0, 1.0), (0.0, 0.0, 0.0)


def entry(red, green, blue, appearances=(), idiom="universal"):
    item = {"color": {"color-space": "srgb",
                      "components": {"alpha": "1.000", "red": red, "green": green, "blue": blue}},
            "idiom": idiom}
    if appearances:
        item["appearances"] = [{"appearance": "luminosity" if a in ("light", "dark") else "contrast", "value": a}
                               for a in appearances]
    return item


def colorset(*entries):
    return {"colors": list(entries), "info": {"author": "xcode", "version": 1}}


class MathTests(unittest.TestCase):
    def test_component_formats(self):
        self.assertEqual(cc.component("0xFF"), 1.0)
        self.assertEqual(cc.component("0x00"), 0.0)
        self.assertEqual(cc.component("0.500"), 0.5)
        self.assertAlmostEqual(cc.component("128"), 128 / 255)
        self.assertEqual(cc.component(1), 1.0)

    def test_known_wcag_ratios(self):
        self.assertEqual(cc.ratio(BLACK, WHITE), 21.0)
        self.assertEqual(cc.ratio(WHITE, BLACK), 21.0)  # order does not matter
        self.assertEqual(cc.ratio(WHITE, WHITE), 1.0)
        # The classic boundary: #767676 passes 4.5:1 on white, #777777 does not.
        self.assertEqual(cc.ratio(cc.hex_rgb("#767676"), WHITE), 4.54)
        self.assertEqual(cc.ratio(cc.hex_rgb("#777777"), WHITE), 4.48)

    def test_unresolved_colors_have_no_ratio(self):
        self.assertIsNone(cc.ratio("system", WHITE))
        self.assertIsNone(cc.ratio(WHITE, None))

    def test_to_hex(self):
        self.assertEqual(cc.to_hex(cc.hex_rgb("#1A2B3C")), "#1A2B3C")
        self.assertEqual(cc.to_hex("system"), "system")
        self.assertEqual(cc.to_hex(None), "None")

    def test_parse_color(self):
        self.assertEqual(cc.parse_color(entry("0xFF", "0x00", "0x00")), (1.0, 0.0, 0.0))
        self.assertEqual(cc.parse_color({"color": {"platform": "ios", "reference": "systemBlueColor"}}), "system")
        self.assertEqual(cc.parse_color({"color": {"platform": "ios"}}), "system")
        self.assertIsNone(cc.parse_color({"idiom": "universal"}))
        self.assertIsNone(cc.parse_color(entry("red", "0", "0")))


class ResolveTests(unittest.TestCase):
    COLORS = {"Foreground/Base": {"light": BLACK, "dark": WHITE},
              "Background/Base": {"light": WHITE, "dark": BLACK},
              "Background/Card": {"light": WHITE, "dark": BLACK}}

    def test_hex_single_and_light_dark(self):
        self.assertEqual(cc.resolve("#000000", {}, "dark"), BLACK)
        self.assertEqual(cc.resolve("#000000/#FFFFFF", {}, "light"), BLACK)
        self.assertEqual(cc.resolve("#000000/#FFFFFF", {}, "dark"), WHITE)
        self.assertIsNone(cc.resolve("#FFF", {}, "light"))

    def test_full_and_unique_short_names(self):
        self.assertEqual(cc.resolve("Foreground/Base", self.COLORS, "light"), BLACK)
        self.assertEqual(cc.resolve("Card", self.COLORS, "dark"), BLACK)
        self.assertIsNone(cc.resolve("Missing", self.COLORS, "light"))

    def test_ambiguous_short_name_is_an_error(self):
        with self.assertRaises(SystemExit) as caught:
            cc.resolve("Base", self.COLORS, "light")
        self.assertIn("Background/Base", str(caught.exception))
        self.assertIn("Foreground/Base", str(caught.exception))


@requires_git
class RepoTests(RepoTestCase):
    def setUp(self):
        super().setUp()
        catalog = "App/Assets.xcassets"
        self.write(f"{catalog}/Foreground/Base.colorset/Contents.json", colorset(
            entry("0x00", "0x00", "0x00"),
            entry("0xFF", "0xFF", "0xFF", ["dark"]),
            entry("0x11", "0x11", "0x11", ["high"]),
            entry("0x80", "0x80", "0x80", idiom="mac"),
        ))
        self.write(f"{catalog}/Background/Base.colorset/Contents.json", colorset(entry("1.000", "1.000", "1.000")))
        self.write(f"{catalog}/Accent.colorset/Contents.json",
                   colorset({"color": {"platform": "ios", "reference": "systemBlueColor"}, "idiom": "universal"}))
        self.write("Other/Shared.xcassets/Accent.colorset/Contents.json", colorset(entry("255", "0", "0")))
        self.write(f"{catalog}/Broken.colorset/Contents.json", "{not json")
        self.commit()

    def test_load_colors(self):
        colors = cc.load_colors(str(self.repo))
        self.assertEqual(sorted(colors), ["Accent", "Background/Base", "Foreground/Base", "Shared:Accent"])
        fg = colors["Foreground/Base"]
        self.assertEqual((fg["light"], fg["dark"]), (BLACK, WHITE))
        self.assertAlmostEqual(fg["light-high-contrast"][0], 0x11 / 255)
        self.assertEqual(colors["Background/Base"]["dark"], WHITE)  # no dark variant: light is used
        self.assertEqual(colors["Accent"]["light"], "system")
        self.assertEqual(colors["Shared:Accent"]["light"], (1.0, 0.0, 0.0))

    def test_pair_command(self):
        result = run_json(self, SCRIPT, "--repo", self.repo, "--pair", "Foreground/Base", "Background/Base",
                          "--pair", "Accent", "#FFFFFF")
        self.assertEqual(result[0]["light"]["ratio"], 21.0)
        self.assertEqual(result[0]["dark"], {"foreground": "#FFFFFF", "background": "#FFFFFF", "ratio": 1.0})
        self.assertIsNone(result[1]["light"]["ratio"])

    def test_list_command_marks_ambiguous_short_names(self):
        rows = {r["name"]: r for r in run_json(self, SCRIPT, "--repo", self.repo, "--list")}
        self.assertTrue(rows["Foreground/Base"]["ambiguous_short_name"])
        self.assertFalse(rows["Accent"]["ambiguous_short_name"])
        text = run_script(SCRIPT, "--repo", self.repo, "--list").stdout
        self.assertIn("4 colors.", text)


if __name__ == "__main__":
    unittest.main()
