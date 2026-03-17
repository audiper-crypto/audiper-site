"""
AUDIPER - Gerador de Avatares Mitologicos 3D
Usa Gemini Imagen 4.0 para gerar os 7 personagens mitologicos corporativos.
"""
import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(r"D:\Site\agno\.env")

from google import genai
from google.genai import types

client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])

OUTPUT_DIR = Path(r"D:\Site\audiper\images\avatars")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Elementos compartilhados para consistencia
SHARED_STYLE = (
    "3D cinematic render, Unreal Engine 5 quality, photorealistic materials "
    "with stylized lighting, octane render aesthetic. "
    "Epic scale, heroic proportions, the figure dominates the frame with commanding presence. "
    "Color palette dominated by black, red neon (#ff3333), and gold (#d4a843). "
    "Deep black environment with volumetric red fog, floating holographic hexagonal grid fragments "
    "in the air around the figure, subtle particle effects of red and gold motes. "
    "8K cinematic render, volumetric lighting, ray tracing, subsurface scattering on skin, "
    "PBR materials, depth of field with bokeh, professional 3D character art for hero section."
)

SHARED_BROOCH = (
    "A glowing red neon brooch on the chest depicting a stylized letter A "
    "inside a hexagonal neural network pattern, emitting soft red neon light (#ff3333). "
)

NEGATIVE = (
    "cartoon, anime, chibi, low quality, blurry, deformed face, extra fingers, "
    "extra limbs, watermark, text overlay, overly bright background, white background, "
    "flat 2D illustration, painting, sketch, low-poly, clay render, comic book style, "
    "pixel art, photographic grain, stock photo aesthetic"
)

AVATARS = [
    {
        "name": "zeus-operacao",
        "prompt": (
            f"{SHARED_STYLE} Three-quarter body shot from head to thighs of Zeus, "
            "king of the Olympian gods reimagined as the supreme CEO overseeing all operations, "
            "three-quarter angle view. Imposing powerful male figure in his late fifties, "
            "commanding presence, broad shoulders, strong weathered face with deep-set piercing "
            "steel-blue eyes, prominent brow, well-groomed silver-white beard trimmed to executive "
            "length, thick silver-white hair swept back with natural authority. Wearing a perfectly "
            "tailored black three-piece suit, visible vest with subtle pinstripe, crisp white shirt "
            f"with a deep red silk tie, gold cufflinks shaped like miniature lightning bolts. {SHARED_BROOCH}"
            "Both hands slightly raised at sides, crackling with contained lightning energy in red "
            "and gold, electrical arcs extending outward to connect with six small holographic screens "
            "floating in a semicircle around him. A subtle golden light halo hovering just above his "
            "head suggesting divine authority. Behind him, suggestion of a high-tech command throne "
            "chair in black leather with red LED accent lines. Expression is commanding, all-seeing, "
            "completely in control. Dramatic cinematic lighting with powerful key light from directly "
            "in front, golden fill light from both sides, strong red rim light from behind."
        ),
    },
    {
        "name": "athena-estrategia",
        "prompt": (
            f"{SHARED_STYLE} Three-quarter body shot from head to thighs of Athena, "
            "the Greek goddess of wisdom reimagined as a powerful female corporate executive, "
            "three-quarter angle view. Striking woman with sharp angular features, olive skin, "
            "dark hair pulled back in a sleek low bun with a single golden hair pin shaped like "
            "an olive branch. Wearing a razor-sharp power suit in black with precise red trim "
            f"along the lapels and pocket edges, structured shoulders conveying authority. {SHARED_BROOCH}"
            "A small mechanical cybernetic owl perched on her left shoulder, crafted from brushed "
            "dark metal and gold, with piercing red LED eyes, tiny articulated wings with visible "
            "micro-circuitry. Her classic Corinthian helmet reimagined as a sleek augmented reality "
            "headset visor, translucent red HUD display visible across her right eye. Her right hand "
            "gestures over a holographic strategy board floating in front of her, displaying a "
            "battlefield-style tactical map with interconnected nodes in red and gold light. "
            "Expression is calculating, confident, gray piercing eyes looking directly at the viewer. "
            "Dramatic cinematic lighting with strong key light from upper right, subtle golden fill "
            "from the left, red rim light from behind."
        ),
    },
    {
        "name": "themis-hardening",
        "prompt": (
            f"{SHARED_STYLE} Three-quarter body shot from head to thighs of Themis, "
            "the Greek goddess of justice reimagined as a senior female auditor and quality "
            "assurance specialist, three-quarter angle view. Distinguished elegant woman in her "
            "late forties with strong refined features, high cheekbones, silver-streaked dark hair "
            "worn in a precise French twist. Wearing a formal tailored business suit in black with "
            f"impeccable cut, structured blazer with gold buttons, crisp white blouse collar. {SHARED_BROOCH}"
            "Her right hand holds up golden scales of justice at eye level, perfectly balanced, "
            "one scale pan contains a glowing green holographic checkmark, the other contains "
            "floating lines of code in red light. Her left hand holds a magnifying glass with "
            "ornate gold frame and a lens that glows with concentrated red energy light. "
            "Her traditional blindfold reimagined as a sleek red-tinted scanning visor band "
            "across her eyes, glowing with a horizontal red LED scan line. Expression is stern, "
            "incorruptible, precise. Dramatic cinematic lighting with cool neutral key light "
            "from directly above, subtle gold fill from the left, red rim light from behind."
        ),
    },
    {
        "name": "hermes-descoberta",
        "prompt": (
            f"{SHARED_STYLE} Three-quarter body shot from head to thighs of Hermes, "
            "the Greek messenger god reimagined as a modern business consultant, "
            "three-quarter angle view. Young athletic male figure with sharp intelligent features, "
            "short curly dark hair with faint golden highlights. Wearing a slim-fit suit that "
            "transitions from deep navy at the shoulders to pure black at the torso, with golden "
            f"winged ornamental details on the suit collar resembling miniature Hermes wings. {SHARED_BROOCH}"
            "His right hand holds a sleek modern glass tablet displaying floating holographic data "
            "visualizations in red and gold. His left hand grips a reimagined caduceus staff, "
            "a slender matte-black tech wand with two serpentine red energy streams coiling around it. "
            "Winged sandals modernized with brushed gold metallic wings and black leather straps. "
            "Expression is curious, alert, eyes scanning to the side as if detecting new information. "
            "Dramatic cinematic lighting with cool key light from upper left, warm golden rim light "
            "from the right, subtle red backlight glow."
        ),
    },
    {
        "name": "prometheus-construcao",
        "prompt": (
            f"{SHARED_STYLE} Three-quarter body shot from head to thighs of Prometheus, "
            "the Titan who brought fire to humanity reimagined as a revolutionary tech developer, "
            "three-quarter angle view. Lean athletic young male figure with sharp intense features, "
            "angular jawline, medium-length dark tousled hair with faint red highlights, pale skin. "
            "Wearing a black hoodie with the hood down, sleeves rolled up to elbows revealing "
            f"muscular forearms. {SHARED_BROOCH}"
            "Both hands cupped together in front of him, palms up, holding a flame made entirely "
            "of swirling digital code and data streams, the fire composed of cascading red and gold "
            "characters and light particles rising upward. On both wrists, thick broken chains hang "
            "with links dangling, break points glowing hot red. On his forearms, circuit board "
            "patterns glow faintly beneath the skin in red and gold lines. Expression is passionate, "
            "revolutionary, eyes burning with conviction. Dramatic cinematic lighting with the "
            "digital fire as primary light source casting warm red-gold light upward onto his face."
        ),
    },
    {
        "name": "hephaestus-fundacao",
        "prompt": (
            f"{SHARED_STYLE} Three-quarter body shot from head to thighs of Hephaestus, "
            "the Greek god of the forge reimagined as a system architect and infrastructure builder, "
            "three-quarter angle view. Broad-shouldered powerfully built male figure with a weathered "
            "strong face, short dark beard with faint silver streaks, intense brown eyes. Wearing a "
            "high-tech architect jacket in black with matte leather-like texture, industrial design "
            f"with subtle gold stitching and angular geometric patterns embossed. {SHARED_BROOCH}"
            "His left arm is cybernetic from the elbow down, matte black prosthetic with visible "
            "gold circuit traces and small red LED nodes pulsing at the joints. His right hand "
            "grips a reimagined forge hammer, a sleek matte-black tool with a glowing red energy "
            "head, mid-swing creating sparks of red and gold digital energy that form circuit board "
            "patterns in the air. Expression is focused, determined, jaw set. Dramatic cinematic "
            "lighting with warm orange-gold key light from below-left suggesting forge fire, "
            "cool blue-gray fill from the right, strong red rim light from behind."
        ),
    },
    {
        "name": "apollo-lancamento",
        "prompt": (
            f"{SHARED_STYLE} Three-quarter body shot from head to thighs of Apollo, "
            "the Greek god of light reimagined as a charismatic creative director orchestrating "
            "a product launch, three-quarter angle view. Strikingly handsome young male figure "
            "with warm golden-bronze skin, wavy medium-length dark hair swept back, bright "
            "captivating eyes that seem to emit faint golden light. Wearing a stylish black dress "
            f"shirt with top two buttons open, sleeves rolled to mid-forearm. {SHARED_BROOCH}"
            "His classic laurel wreath reimagined as a sleek glowing circlet headband around his "
            "forehead, intertwining red and gold energy filaments forming leaf-like patterns of "
            "light. His right hand raised upward with palm open, emitting expanding rays of red "
            "and gold light radiating outward like a dawn burst, light rays containing tiny data "
            "particles. His left hand holds a reimagined lyre, now a futuristic compact amplifier "
            "in matte black and gold. Expression is charismatic, radiant, inspiring, confident open "
            "smile. Dramatic cinematic lighting with strong warm golden key light from upper right, "
            "cool blue fill from the left, red rim light from behind."
        ),
    },
]

def generate_avatar(avatar_data, model="imagen-4.0-generate-001"):
    """Gera um avatar e salva no diretorio de output."""
    name = avatar_data["name"]
    prompt = avatar_data["prompt"]
    output_path = OUTPUT_DIR / f"{name}.png"

    if output_path.exists():
        print(f"  [SKIP] {name} - ja existe")
        return True

    print(f"  [GEN] {name}...")
    try:
        response = client.models.generate_images(
            model=model,
            prompt=prompt,
            config=types.GenerateImagesConfig(
                number_of_images=1,
                aspect_ratio="3:4",
                safety_filter_level="BLOCK_LOW_AND_ABOVE",
                person_generation="ALLOW_ADULT",
            ),
        )

        if response.generated_images:
            img = response.generated_images[0]
            with open(output_path, "wb") as f:
                f.write(img.image.image_bytes)
            size_kb = output_path.stat().st_size / 1024
            print(f"  [OK] {name} - {size_kb:.0f}KB salvo")
            return True
        else:
            print(f"  [WARN] {name} - nenhuma imagem retornada (possivel filtro de seguranca)")
            return False

    except Exception as e:
        print(f"  [ERR] {name} - {e}")
        return False


def main():
    print("=" * 60)
    print("  AUDIPER - Geracao de Avatares Mitologicos 3D")
    print(f"  Modelo: Gemini Imagen 4.0")
    print(f"  Output: {OUTPUT_DIR}")
    print("=" * 60)
    print()

    results = {}
    for i, avatar in enumerate(AVATARS, 1):
        print(f"[{i}/7] {avatar['name']}")
        success = generate_avatar(avatar)
        results[avatar["name"]] = success
        if i < len(AVATARS):
            time.sleep(2)  # Rate limit buffer

    print()
    print("=" * 60)
    ok = sum(1 for v in results.values() if v)
    fail = sum(1 for v in results.values() if not v)
    print(f"  Resultados: {ok} OK, {fail} falhas")
    for name, success in results.items():
        status = "OK" if success else "FALHA"
        print(f"    {status}: {name}")
    print("=" * 60)

    return 0 if fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
