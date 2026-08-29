import json
import os
import urllib.request
from pathlib import Path

USERNAME = os.environ["GITHUB_USER_NAME"]
TOKEN = os.environ["GITHUB_TOKEN"]

OUTPUT_DIR = Path("dist")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

QUERY = """
query($login:String!) {
  user(login:$login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            contributionCount
            date
          }
        }
      }
    }
  }
}
"""

request = urllib.request.Request(
    "https://api.github.com/graphql",
    data=json.dumps({
        "query": QUERY,
        "variables": {
            "login": USERNAME
        }
    }).encode("utf-8"),
    headers={
        "Authorization": f"bearer {TOKEN}",
        "Content-Type": "application/json",
        "User-Agent": "github-contribution-snake"
    }
)

with urllib.request.urlopen(request) as response:
    result = json.load(response)

if result.get("errors"):
    raise RuntimeError(result["errors"])

calendar = (
    result["data"]["user"]
    ["contributionsCollection"]
    ["contributionCalendar"]
)

weeks = calendar["weeks"]

# ---------------------------------------------------------
# Canvas
# ---------------------------------------------------------

WIDTH = 960
HEIGHT = 190

LEFT = 24
TOP = 30

CELL = 12
GAP_X = 5
GAP_Y = 5

STEP_X = CELL + GAP_X
STEP_Y = CELL + GAP_Y

# ---------------------------------------------------------
# Contribution background
# ---------------------------------------------------------

counts = []

for week in weeks:
    for day in week["contributionDays"]:
        counts.append(day["contributionCount"])

maximum = max(counts or [1])

background_cells = []

for x, week in enumerate(weeks[:53]):

    for y, day in enumerate(week["contributionDays"][:7]):

        count = day["contributionCount"]

        if count == 0:
            color = "#151A21"
        elif count <= maximum * 0.20:
            color = "#251B35"
        elif count <= maximum * 0.40:
            color = "#382052"
        elif count <= maximum * 0.65:
            color = "#573078"
        elif count <= maximum * 0.85:
            color = "#7941A5"
        else:
            color = "#9B5DE5"

        x_pos = LEFT + x * STEP_X
        y_pos = TOP + y * STEP_Y

        background_cells.append(
            f"""
            <rect
                x="{x_pos}"
                y="{y_pos}"
                width="{CELL}"
                height="{CELL}"
                rx="3"
                fill="{color}"
            />
            """
        )

# ---------------------------------------------------------
# Snake path
#
# The snake travels through the same 53 x 7 area as the
# contribution graph, but follows a smooth curved route.
# ---------------------------------------------------------

points = []

for x in range(min(53, len(weeks))):

    if x % 2 == 0:
        rows = range(7)
    else:
        rows = range(6, -1, -1)

    for y in rows:

        x_pos = LEFT + x * STEP_X + CELL / 2
        y_pos = TOP + y * STEP_Y + CELL / 2

        points.append((x_pos, y_pos))


def create_smooth_path(points):

    if not points:
        return ""

    path = f"M {points[0][0]:.2f} {points[0][1]:.2f}"

    for i in range(1, len(points)):

        previous = points[i - 1]
        current = points[i]

        px, py = previous
        cx, cy = current

        # Curved transitions between grid columns
        if px != cx:

            direction = 1 if cy > py else -1

            control_x = px + (cx - px) * 0.5
            control_y = py + direction * STEP_Y * 0.75

            path += (
                f" Q {control_x:.2f} {control_y:.2f} "
                f"{cx:.2f} {cy:.2f}"
            )

        else:

            path += f" L {cx:.2f} {cy:.2f}"

    return path


snake_path = create_smooth_path(points)

# ---------------------------------------------------------
# Snake body
# ---------------------------------------------------------

body_segments = []

SEGMENTS = 22

for index in range(SEGMENTS):

    radius = max(5.5, 9.0 - index * 0.14)

    delay = index * 0.18

    opacity = max(0.35, 1.0 - index * 0.025)

    body_segments.append(
        f"""
        <circle
            r="{radius:.2f}"
            fill="url(#snakeGradient)"
            stroke="#C084FC"
            stroke-width="0.65"
            opacity="{opacity:.2f}"
        >
            <animateMotion
                dur="24s"
                begin="-{delay:.2f}s"
                repeatCount="indefinite"
                rotate="auto">

                <mpath href="#snakePath"/>

            </animateMotion>
        </circle>
        """
    )

# ---------------------------------------------------------
# SVG
# ---------------------------------------------------------

svg = f"""
<svg
    xmlns="http://www.w3.org/2000/svg"
    width="100%"
    viewBox="0 0 {WIDTH} {HEIGHT}"
    role="img"
    aria-label="Animated GitHub contribution snake">

    <defs>

        <linearGradient
            id="snakeGradient"
            x1="0"
            y1="0"
            x2="1"
            y2="1">

            <stop
                offset="0%"
                stop-color="#E9D5FF"/>

            <stop
                offset="40%"
                stop-color="#A855F7"/>

            <stop
                offset="100%"
                stop-color="#5B21B6"/>

        </linearGradient>

        <filter
            id="snakeGlow"
            x="-80%"
            y="-80%"
            width="260%"
            height="260%">

            <feGaussianBlur
                stdDeviation="1.8"
                result="blur"/>

            <feMerge>

                <feMergeNode in="blur"/>

                <feMergeNode in="SourceGraphic"/>

            </feMerge>

        </filter>

        <path
            id="snakePath"
            d="{snake_path}"
            fill="none"/>

    </defs>

    <!-- Background -->

    <rect
        width="100%"
        height="100%"
        rx="16"
        fill="#0D1117"/>

    <!-- Contribution grid -->

    {''.join(background_cells)}

    <!-- Subtle route -->

    <path
        d="{snake_path}"
        fill="none"
        stroke="#3B2754"
        stroke-width="2"
        opacity="0.28"/>

    <!-- Snake body -->

    {''.join(body_segments)}

    <!-- Snake head -->

    <g filter="url(#snakeGlow)">

        <g>

            <ellipse
                cx="0"
                cy="0"
                rx="11"
                ry="8"
                fill="url(#snakeGradient)"
                stroke="#E9D5FF"
                stroke-width="0.9">

                <animateMotion
                    dur="24s"
                    repeatCount="indefinite"
                    rotate="auto">

                    <mpath href="#snakePath"/>

                </animateMotion>

            </ellipse>

            <!-- Eye -->

            <circle
                cx="5"
                cy="-3"
                r="1.7"
                fill="#FFFFFF">

                <animateMotion
                    dur="24s"
                    repeatCount="indefinite"
                    rotate="auto">

                    <mpath href="#snakePath"/>

                </animateMotion>

            </circle>

            <circle
                cx="5"
                cy="-3"
                r="0.7"
                fill="#111827">

                <animateMotion
                    dur="24s"
                    repeatCount="indefinite"
                    rotate="auto">

                    <mpath href="#snakePath"/>

                </animateMotion>

            </circle>

            <!-- Forked tongue -->

            <path
                d="
                    M 9 1
                    Q 14 2 18 1
                    M 17 1 L 20 -1
                    M 17 1 L 20 3
                "
                fill="none"
                stroke="#F0ABFC"
                stroke-width="0.85"
                stroke-linecap="round">

                <animateMotion
                    dur="24s"
                    repeatCount="indefinite"
                    rotate="auto">

                    <mpath href="#snakePath"/>

                </animateMotion>

            </path>

        </g>

    </g>

</svg>
"""

output_file = OUTPUT_DIR / "github-contribution-snake.svg"

output_file.write_text(
    svg,
    encoding="utf-8"
)

print(
    f"Generated {output_file} "
    f"for {USERNAME} "
    f"({calendar['totalContributions']} contributions)"
)
