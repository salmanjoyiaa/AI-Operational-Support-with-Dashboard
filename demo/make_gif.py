from PIL import Image
import glob

frames = []
order = [
    'demo/frame-home.png',
    'demo/frame-tickets.png',
    'demo/frame-ticket-6.png',
    'demo/frame-kb.png',
    'demo/frame-analytics.png'
]
for p in order:
    try:
        im = Image.open(p).convert('RGBA')
        frames.append(im)
    except Exception as e:
        print('skip', p, e)

if not frames:
    raise SystemExit('no frames')

# Resize to common size (use first frame size)
w, h = frames[0].size
frames = [f.resize((w,h), Image.LANCZOS) for f in frames]

out_path = 'demo/demo.gif'
frames[0].save(out_path, save_all=True, append_images=frames[1:], duration=900, loop=0, disposal=2)
print('wrote', out_path)
