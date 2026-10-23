# target texture -> (reference sprite, subject description). One generation each.
STYLE = ("Redraw the reference image as {subj}. Keep EXACTLY the reference's framing, size within the square, pose/orientation, "
         "camera angle and line weight. Art style must match the reference: official Nintendo 'Hello, Mario' sticker style, flat vector "
         "illustration, one bold uniform dark charcoal-brown outline (#4f4846) around every shape, flat solid colour fills, at most one small "
         "simple white highlight, no gradients, no shading, no texture, no text, no drop shadow. Pure plain white background, nothing else in the image.")
JOBS = {
 'FaceEventMushroom00': ('FaceEventMushroom00', "a Pokémon Rare Candy (the light-blue wrapped candy with a rounded centre and twisted wrapper ends on both sides, pale blue with a darker blue wrapper)"),
 'FaceEventStar00':     ('FaceEventStar00', "a Pokémon Thunder Stone: a rounded green crystal stone with a yellow lightning bolt pattern inside it, with two small cute oval black eyes like the reference star"),
 'FaceEventHatenaBlock00': ('FaceEventHatenaBlock00', "a Pokémon Mystery Gift present: a square gift box seen straight on, red and white like a Poké Ball (top half red, bottom half white, black horizontal band) with a small round white button in the centre and a yellow ribbon bow at the top"),
 'FaceEventKuribo00':   ('FaceEventKuribo00', "the Pokémon Rattata (purple rat, big front teeth, cream belly, long curled tail, angry-cute expression), same facing and pose as the reference"),
 'FaceEventTeresa00':   ('FaceEventTeresa00', "the Pokémon Gastly (a black-purple round ghost ball face with a lavender gas aura around it, big grinning mouth with two fangs, slanted eyes), with the same mischievous laughing expression as the reference"),
 'FaceEventTeresa01':   ('FaceEventTeresa01', "the Pokémon Gastly (black-purple round ghost ball face with a lavender gas aura), with the same expression as the reference (grinning, tongue showing)"),
 'FaceEventTeresa02':   ('FaceEventTeresa02', "the Pokémon Gastly (black-purple round ghost ball face with a lavender gas aura), shy and hiding, eyes closed, pink blushing cheeks, the same shy pose as the reference"),
 'FaceEventTeresa03':   ('FaceEventTeresa03', "the Pokémon Gastly (black-purple round ghost ball face with a lavender gas aura), laughing wide open mouth with fangs like the reference"),
 'FaceEventTeresa04':   ('FaceEventTeresa04', "the Pokémon Gastly (black-purple round ghost ball face with a lavender gas aura), shy with eyes closed, blushing pink cheeks, slightly turned like the reference"),
 'FaceEventPukupuku00': ('FaceEventPukupuku00', "the Pokémon Magikarp (orange-red fish, big round blank eyes, pink lips, yellow whiskers, white-yellow fins, crown-like dorsal fin), facing and flapping like the reference"),
 'FaceEventPukupuku01': ('FaceEventPukupuku01', "the Pokémon Magikarp (orange-red fish, big round blank eyes, pink lips, yellow whiskers, white-yellow fins, crown-like dorsal fin), same angle and fin pose as the reference"),
 'FaceEventPukupuku02': ('FaceEventPukupuku02', "the Pokémon Magikarp (orange-red fish, big round blank eyes, pink lips, yellow whiskers, white-yellow fins, crown-like dorsal fin), same angle and fin pose as the reference"),
 'FaceEventGesso00':    ('FaceEventGesso00', "the Pokémon Tentacool (translucent-looking light blue jellyfish body with two red gems, white beak, two long blue tentacles), drawn upright in the same tall pose as the reference"),
 'FaceEventGessoMini00': ('FaceEventGessoMini00', 'a tiny simple Pokémon Tentacool: a light-blue dome-shaped jellyfish head with two round red gems on top and a small white beak, and EXACTLY TWO long blue tentacles hanging down (not more)'),
 'FaceEventBomb00': ('FaceEventBomb00', "the Pokémon Voltorb ONLY: a simple perfect sphere, top half red, bottom half white, thin dark band between, two angry eyes on the red half and a small white shine. It has NO legs, NO feet, NO fuse, NO wind-up key, NO arms. Centred where the bomb's round body is in the reference"),
 'FaceEventDokanNokonoko00': ('FaceEventDokanNokonoko00', "the Pokémon Diglett (brown mole, big pink nose, small black eyes) popping up, same position and crop as the reference (cut off at the bottom edge)"),
 'FaceEventDokanNokonoko01': ('FaceEventDokanNokonoko01', "the Pokémon Diglett (brown mole, big pink nose, small black eyes) popping up and leaning like the reference, cut off at the bottom edge"),
 'FaceEventDokanPakkun00':   ('FaceEventDokanPakkun00', "the Pokémon Bellsprout (yellow bell-shaped head with pink mouth, thin green stem body, two green leaves), mouth closed, same position and crop as the reference"),
 'FaceEventDokanPakkun01':   ('FaceEventDokanPakkun01', "the Pokémon Bellsprout (yellow bell-shaped head with pink mouth, thin green stem body, two green leaves), mouth wide open and leaning like the reference"),
 'FaceEventApple00':    ('FaceEventApple00', "a Pokémon Oran Berry (round blue berry with a green leafy top and darker blue segments)"),
 'FaceEventCap01':      ('FaceEventCap01', "Ash Ketchum's original red and white baseball cap seen from the front (red cap, white front panel with a green 'L'-like league symbol replaced by a simple green arc logo), same shape and angle as the reference cap"),
 'FaceEventNoteBlock00':('FaceEventNoteBlock00', "Jigglypuff's microphone (a round pink marker-style microphone with a black tip), standing upright centred in the same rounded-square frame as the reference"),
 'FaceEventToad00':     ('FaceEventToad00', "the Pokémon Eevee seen from BEHIND (back view, big ears, fluffy cream neck ruff, bushy tail with cream tip), standing, same size and placement as the reference"),
 'FaceEventToad02':     ('FaceEventToad02', "the Pokémon Eevee seen from the front, happy, waving one front paw, standing on hind legs, same size and placement as the reference"),
 'FaceEventToadHand00': ('FaceEventToadHand00', 'one Eevee front leg raised and waving: a short furry brown foreleg ending in a soft rounded animal paw with NO fingers and NO thumb, same angle as the reference arm'),
 'FaceBtnCamera00': ('FaceBtnCamera00', "the Pokémon Eevee standing behind/next to the same grey camera on a tripod, waving one paw, replacing Toad; keep the camera and tripod exactly as in the reference. NO background circle or disc behind Eevee, only pure white background"),
}
