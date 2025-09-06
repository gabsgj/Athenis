from app.models.prompt_manager import PromptManager

def test_prompt_build():
    pm = PromptManager()
    p = pm.build('simplify', 'Hello world')
    assert 'Plain-language' in p or 'Plain-language'.lower() in p.lower()
