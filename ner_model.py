from transformers import pipeline

ner = pipeline("ner", model="jjzha/jobbert_knowledge_extraction", grouped_entities=True)

def find_skill_section(lines):
    max_lines = 15
    skills_text = []
    capture_skills_section =False
    for line in lines:
        if "skills" in line.lower():
            capture_skills_section = True

        if capture_skills_section:
            skills_text.append(line)
        
        if len(skills_text) > max_lines:
            break

    text = "\n".join(skills_text)
    return text

def ner_model(data): 
    lines = data.split("\n")
    text = find_skill_section(lines)   
    
    results = ner(text)
    skills = reconstruct_bio_entities(results)

    print(" Extracted Skills from NER model:")
    for skill in skills:
        print("-", skill)
    return skills


def reconstruct_bio_entities(entities, min_score=0.9):
    skills = []
    current_phrase = []

    for ent in entities:
        word = ent["word"]
        label = ent["entity_group"]
        score = ent["score"]

        # Skip low confidence tokens
        if score < min_score:
            continue

        # Handle subword tokens (e.g., ##s)
        if word.startswith("##"):
            word = word[2:]
            if current_phrase:
                current_phrase[-1] += word
            continue

        if label == "B":
            if current_phrase:
                skills.append(" ".join(current_phrase))
            current_phrase = [word]
        elif label == "I":
            current_phrase.append(word)
            
    # Append the last phrase
    if current_phrase:
        skills.append(" ".join(current_phrase))

    return list(set(skills)) 