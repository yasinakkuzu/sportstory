import os

# 1. Gemini'yi Çalışan Modele (1.5 Flash) Geri Al
weaver_path = "engine/agents/scriptweaver_agent.py"
if os.path.exists(weaver_path):
    with open(weaver_path, "r", encoding="utf-8") as f: 
        content = f.read()
    content = content.replace("model='gemini-2.5-flash'", "model='gemini-1.5-flash'")
    with open(weaver_path, "w", encoding="utf-8") as f: 
        f.write(content)

# 2. Orkestratördeki İsim Uyuşmazlığını (SubtitleWorker) Temizle
gen_path = "generate_short.py"
if os.path.exists(gen_path):
    with open(gen_path, "r", encoding="utf-8") as f: 
        content = f.read()
    
    old_block = """    from engine.subtitles import SubtitleWorker, KineticSubtitleRenderer"""
    new_block = """    from engine.subtitles import KineticSubtitleRenderer
    try:
        from engine.workers.subtitle_worker import SubtitleWorker
    except ImportError:
        pass"""
        
    if old_block in content:
        content = content.replace(old_block, new_block)
        with open(gen_path, "w", encoding="utf-8") as f: 
            f.write(content)

print("✅ SİSTEM BAŞARIYLA ONARILDI!")
