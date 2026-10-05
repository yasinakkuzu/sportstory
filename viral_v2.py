import os
import subprocess

print("==================================================")
print("🚀 SPORTSTORY: VİRAL 2.0 & SES GÜNCELLEMESİ")
print("==================================================")

print("1/4: Yeni Oyun Videoları (Minecraft ve ASMR) İndiriliyor (1-2 dk sürebilir)...")
bg_vids = {
    "bg_minecraft.mp4": "ytsearch1:minecraft parkour gameplay no copyright 1 hour",
    "bg_asmr.mp4": "ytsearch1:satisfying kinetic sand no copyright 1 hour"
}
for fname, query in bg_vids.items():
    if not os.path.exists(fname):
        print(f"📥 İndiriliyor: {fname}")
        subprocess.run(f'python3 -m yt_dlp -f "bestvideo[height<=1080][ext=mp4]/best" -o "{fname}" "{query}"', shell=True, stdout=subprocess.DEVNULL)

print("2/4: Senarist Ajana 'İlk Sahnede Konuyu Ver' kuralı ekleniyor...")
sw_path = "engine/agents/scriptweaver_agent.py"
with open(sw_path, "r", encoding="utf-8") as f:
    sw = f.read()

old_prompt = "KIRILMAZ KURALLAR: 1. Tam 5 sahne olmalı. 2. Asla uzun cümle kurma. Her sahne MAKSİMUM 3-5 KELİME olmalı (Hızlı ve şok edici). 3. CTA ASLA 1,2,3,4. sahnelerde kullanılamaz."
new_prompt = "KIRILMAZ KURALLAR: 1. Konunun KİMİNLE VEYA HANGİ TAKIMLA ilgili olduğu KESİNLİKLE 1. SAHNEDE söylenecek! 2. Tam 5 sahne olmalı. 3. Asla uzun cümle kurma, her sahne MAKSİMUM 3-5 KELİME olmalı. 4. CTA ASLA 1,2,3,4. sahnelerde kullanılamaz."

sw = sw.replace(old_prompt, new_prompt)
with open(sw_path, "w", encoding="utf-8") as f:
    f.write(sw)

print("3/4: Altyazı Motorunda Tipografi Kontrastı Güçlendiriliyor...")
sub_path = "engine/subtitles.py"
if os.path.exists(sub_path):
    with open(sub_path, "r", encoding="utf-8") as f:
        subs = f.read()
    subs = subs.replace("stroke_width = 3 if is_act else 2", "stroke_width = 9 if is_act else 5")
    with open(sub_path, "w", encoding="utf-8") as f:
        f.write(subs)

print("4/4: Orkestratör (Karartma, Rotasyon, Hızlı & Tok Ses) Güncelleniyor...")
gen_path = "generate_short.py"
with open(gen_path, "r", encoding="utf-8") as f:
    gen = f.read()

# Arkaplan Havuzu
if 'master_bg = "master_bg.mp4"' in gen:
    gen = gen.replace('master_bg = "master_bg.mp4"', '''bg_list = ["master_bg.mp4", "bg_minecraft.mp4", "bg_asmr.mp4"]
        import random
        valid_bgs = [bg for bg in bg_list if os.path.exists(bg)]
        master_bg = random.choice(valid_bgs) if valid_bgs else "master_bg.mp4"''')

# Yeni Ses (Salih ve Hız)
if 'self.audio_worker.generate_voiceover(script=full_text, target_path=str(raw_voice_path), language=lang)' in gen:
    gen = gen.replace(
        'self.audio_worker.generate_voiceover(script=full_text, target_path=str(raw_voice_path), language=lang)',
        'self.audio_worker.generate_voiceover(script=full_text, target_path=str(raw_voice_path), language=lang, voice="tr-TR-SalihNeural" if lang=="tr" else "en-US-SteffanNeural", rate="+15%")'
    )

# Karartma Filtresi
old_comp = 'final_frame = Image.alpha_composite(frame_img, sub_overlay).convert("RGB")'
new_comp = '''dark_overlay = Image.new("RGBA", (1080, 1920), (0, 0, 0, 75))
                    frame_img = Image.alpha_composite(frame_img, dark_overlay)
                    final_frame = Image.alpha_composite(frame_img, sub_overlay).convert("RGB")'''
if old_comp in gen:
    gen = gen.replace(old_comp, new_comp)

with open(gen_path, "w", encoding="utf-8") as f:
    f.write(gen)

print("\n✅ SİSTEM BAŞARIYLA VİRAL 2.0 (YENİ SES & EFEKTLER) SÜRÜMÜNE GÜNCELLENDİ!")
