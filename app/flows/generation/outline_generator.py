# Modernized for DSPy + CoT + Reflection, July 2024
# Updated with Book Title Generation
# If you don't have DSPy, install it with: pip install dspy

import os
import json
import time
from typing import Dict, Any
import dspy
from app.core.logger_config import setup_logger

logger = setup_logger(__name__)

# Placeholder for loading examples (for future optimizer use)
EXAMPLES_PATH = os.path.join(os.path.dirname(__file__), 'story_outline_examples.json')

# Set up your LLM (replace with your API key and model)
from app.core.config import get_settings
settings = get_settings()

if not settings.OPENAI_API_KEY:
    logger.error("❌ OPENAI_API_KEY not found in environment variables")
    raise ValueError("OPENAI_API_KEY environment variable is required")

lm = dspy.LM('openai/gpt-4o-mini', api_key=settings.OPENAI_API_KEY, temperature=0.7, max_tokens=3000)
dspy.configure(lm=lm)

# Define signatures for DSPy
class GenerateStory(dspy.Signature):
    """You are a world-class novelist and story architect.

    Step 1: Analyze the user's story idea and identify the genre, tone, and main conflict.
    Step 2: Brainstorm 2-3 possible story arcs or directions for this idea.
    Step 3: Select the most engaging arc.
    Step 4: Write a cinematic, emotionally engaging summary of the story (like a back-cover blurb or movie trailer), ending with a compelling hook or cliffhanger. Do NOT provide a chapter-by-chapter breakdown.

    Your output should be a single, engaging summary (3-5 sentences) that teases the story and ends with a hook."""
    
    idea = dspy.InputField(desc="The user's story idea")
    analysis = dspy.OutputField(desc="Step 1: Analysis of genre, tone, and main conflict")
    story_arcs = dspy.OutputField(desc="Step 2: 2-3 possible story directions brainstormed")
    selected_arc = dspy.OutputField(desc="Step 3: The most engaging arc chosen with reasoning")
    summary = dspy.OutputField(desc="Step 4: Cinematic story summary with hook (3-5 sentences)")

class GenerateChapterBreakdown(dspy.Signature):
    """You are a professional story structure expert creating detailed chapter breakdowns.
    
    Based on the story summary and genre, create a comprehensive chapter-by-chapter breakdown.
    
    Create 8-15 chapters depending on the story complexity. Each chapter should have:
    1. A compelling chapter title
    2. 3-5 key plot points or events
    3. Character arcs and development
    4. Setting and atmosphere details
    5. Cliffhanger or transition to next chapter
    
    IMPORTANT: Also extract and return the main characters and key locations as simple arrays.
    
    Format as a JSON object with the following structure:
    {
      "chapters": [
        {
          "chapter_number": 1,
          "title": "Chapter Title",
          "key_events": ["Event 1", "Event 2", "Event 3"],
          "character_development": "Description of character growth",
          "setting": "Setting description and atmosphere",
        }
      ],
      "main_characters": [eg., "Alex", "Clara", "Maya"],
      "key_locations": [eg., "Coffee Shop", "Library", "Office"]
    }
    
    Return ONLY valid JSON format, no additional text."""
    
    summary = dspy.InputField(desc="The story summary to break down")
    genre = dspy.InputField(desc="The story genre")
    tone = dspy.InputField(desc="The story tone")
    chapter_breakdown = dspy.OutputField(desc="JSON object with chapters, main_characters array, and key_locations array")

class ReflectOnStory(dspy.Signature):
    """You are a professional story editor. Review the following story summary for:
    - Logical flow and coherence
    - Genre and tone match
    - Presence of a strong hook or cliffhanger
    - Overall engagement

    If the summary is strong, reply: 'PASS'
    If not, reply: 'REVISE' and briefly state what to improve."""
    
    summary = dspy.InputField(desc="The story summary to evaluate")
    evaluation = dspy.OutputField(desc="Detailed assessment of flow, genre match, hook strength, engagement")
    verdict = dspy.OutputField(desc="Either 'PASS' or 'REVISE' with brief reasoning")

class ExtractMetadata(dspy.Signature):
    """Extract genre, tone, and generate an engaging book title from story summary.
    
    The book title should be:
    - Memorable and marketable 
    - 2-6 words long
    - Capture the story's essence
    - Genre-appropriate
    - Emotionally engaging
    - Similar to successful books in the same genre"""
    
    summary = dspy.InputField(desc="The story summary")
    genre = dspy.OutputField(desc="Primary genre of the story")
    tone = dspy.OutputField(desc="Overall tone of the story")
    book_title = dspy.OutputField(desc="Compelling, marketable book title (2-6 words)")

# Global optimized generator cache
_optimized_generator = None
_last_optimization_time = None
_optimization_examples_count = 0

def get_optimized_generator(force_reoptimize=False):
    """Get cached optimized generator or create new one if needed."""
    global _optimized_generator, _last_optimization_time, _optimization_examples_count
    
    generator = OutlineGenerator()
    current_examples_count = len(generator.examples)
    
    # Check if we need to (re)optimize
    should_optimize = (
        force_reoptimize or 
        _optimized_generator is None or 
        current_examples_count != _optimization_examples_count or
        (_last_optimization_time and 
         (time.time() - _last_optimization_time) > 3600)  # Re-optimize every hour
    )
    
    if should_optimize and generator.examples:
        print(f"🔧 Optimizing prompts using {current_examples_count} examples...")
        try:
            _optimized_generator = generator.optimize()
            _last_optimization_time = time.time()
            _optimization_examples_count = current_examples_count
            print("✅ Optimization completed and cached!")
        except Exception as e:
            print(f"❌ Optimization failed: {e}")
            _optimized_generator = generator
    elif _optimized_generator is None:
        _optimized_generator = generator
        
    return _optimized_generator

def load_examples():
    """Load training examples and convert to DSPy format."""
    examples = []
    try:
        if os.path.exists(EXAMPLES_PATH):
            with open(EXAMPLES_PATH, 'r', encoding='utf-8') as f:
                raw_examples = json.load(f)
                
            # Convert to DSPy Example format
            for ex in raw_examples:
                # Include book_title in training examples if available
                example_data = {
                    "idea": ex["idea"],
                    "summary": ex["summary"],
                    "genre": ex["genre"], 
                    "tone": ex["tone"]
                }
                
                # Add book_title if it exists in the example
                if "title" in ex:
                    example_data["book_title"] = ex["title"]
                elif "book_title" in ex:
                    example_data["book_title"] = ex["book_title"]
                
                dspy_example = dspy.Example(**example_data).with_inputs("idea")
                examples.append(dspy_example)
                
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Warning: Could not load examples from {EXAMPLES_PATH}: {e}")
    return examples

def save_new_example(idea: str, summary: str, genre: str, tone: str, book_title: str = None):
    """Save a new example to the JSON file for future training."""
    new_example = {
        "idea": idea,
        "summary": summary, 
        "genre": genre,
        "tone": tone,
        "title": book_title or "Untitled Story"  # Include book_title in training data
    }
    
    try:
        # Load existing examples
        existing_examples = []
        if os.path.exists(EXAMPLES_PATH):
            with open(EXAMPLES_PATH, 'r', encoding='utf-8') as f:
                existing_examples = json.load(f)
        
        # Add new example
        existing_examples.append(new_example)
        
        # Save back to file
        with open(EXAMPLES_PATH, 'w', encoding='utf-8') as f:
            json.dump(existing_examples, f, indent=2)
            
        print(f"Saved new example with title '{book_title}' to {EXAMPLES_PATH}")
        
    except Exception as e:
        print(f"Error saving example: {e}")

def metric_function(example, pred, trace=None):
    """Custom metric to evaluate story generation quality."""
    # Check if summary exists and is reasonable length
    if not pred.summary or len(pred.summary.strip()) < 50:
        return 0.0
    
    # Check if genre and tone match (if we have ground truth)
    genre_match = 1.0 if hasattr(example, 'genre') and example.genre.lower() in pred.genre.lower() else 0.5
    tone_match = 1.0 if hasattr(example, 'tone') and example.tone.lower() in pred.tone.lower() else 0.5
    
    # Check book title quality (if we have ground truth)
    title_score = 0.8  # Default score
    if hasattr(pred, 'book_title') and pred.book_title:
        # Check if title is reasonable length (2-6 words)
        title_words = len(pred.book_title.split())
        if 2 <= title_words <= 6:
            title_score = 1.0
        # Check if title matches ground truth (if available)
        if hasattr(example, 'book_title') and example.book_title:
            # Simple similarity check
            if pred.book_title.lower() in example.book_title.lower() or example.book_title.lower() in pred.book_title.lower():
                title_score = 1.0
    
    # Check for hook/cliffhanger (simple heuristic)
    hook_indicators = ['?', '!', '...', 'but', 'however', 'until', 'when', 'if', 'unless']
    has_hook = any(indicator in pred.summary.lower() for indicator in hook_indicators)
    hook_score = 1.0 if has_hook else 0.7
    
    # Check length (3-5 sentences roughly 100-400 chars)
    length_score = 1.0 if 100 <= len(pred.summary) <= 400 else 0.8
    
    return (genre_match + tone_match + title_score + hook_score + length_score) / 5.0

class OutlineGenerator(dspy.Module):
    def __init__(self):
        super().__init__()
        self.generate_story = dspy.ChainOfThought(GenerateStory)
        self.extract_metadata = dspy.ChainOfThought(ExtractMetadata)
        self.generate_chapters = dspy.ChainOfThought(GenerateChapterBreakdown)
        self.reflect = dspy.ChainOfThought(ReflectOnStory)
        self.examples = load_examples()
        self.is_optimized = False

    def forward(self, idea, include_chapters=True):
        # Generate initial story summary
        story_result = self.generate_story(idea=idea)
        
        # Extract metadata
        metadata_result = self.extract_metadata(summary=story_result.summary)
        
        # Generate chapter breakdown with characters and locations
        if include_chapters:
            chapter_result = self.generate_chapters(
                summary=story_result.summary,
                genre=metadata_result.genre,
                tone=metadata_result.tone
            )
            
            # Parse the JSON response
            try:
                import json
                chapter_data = json.loads(chapter_result.chapter_breakdown)
                
                # Extract the components
                chapters = chapter_data.get("chapters", [])
                main_characters = chapter_data.get("main_characters", [])
                key_locations = chapter_data.get("key_locations", [])
                
            except json.JSONDecodeError as e:
                # Fallback if JSON parsing fails
                print(f"Failed to parse chapter JSON: {e}")
                chapters = []
                main_characters = []
                key_locations = []
        else:
            chapters = []
            main_characters = []
            key_locations = []
        
        # Reflect on the story
        reflection_result = self.reflect(summary=story_result.summary)
        
        return dspy.Prediction(
            summary=story_result.summary,
            genre=metadata_result.genre,
            tone=metadata_result.tone,
            book_title=metadata_result.book_title,
            reflection=reflection_result.evaluation,
            chapter_breakdown=chapters,
            main_characters=main_characters,  # NEW: Characters from LLM
            key_locations=key_locations       # NEW: Locations from LLM
        )

    def _parse_text_to_chapters(self, text_breakdown):
        """Convert unstructured text breakdown to structured format."""
        import re
        
        chapters = []
        # Split by chapter headings (### Chapter X:)
        chapter_sections = re.split(r'###\s*Chapter\s*(\d+):', text_breakdown)
        
        for i in range(1, len(chapter_sections), 2):  # Skip first empty split
            if i + 1 < len(chapter_sections):
                chapter_num = int(chapter_sections[i])
                chapter_content = chapter_sections[i + 1].strip()
                
                # Extract title (first line)
                lines = chapter_content.split('\n')
                title = lines[0].strip() if lines else f"Chapter {chapter_num}"
                
                # Extract key events, character development, setting, cliffhanger
                key_events = []
                character_development = ""
                setting = ""
                cliffhanger = ""
                
                for line in lines[1:]:
                    line = line.strip()
                    if '**Key Events**' in line or '- **Key Events**' in line:
                        # Extract events from following text
                        event_text = line.split('**Key Events**')[-1].strip(': -')
                        if event_text:
                            key_events.append(event_text)
                    elif '**Character Development**' in line:
                        character_development = line.split('**Character Development**')[-1].strip(': -')
                    elif '**Setting**' in line:
                        setting = line.split('**Setting**')[-1].strip(': -')
                    elif '**Cliffhanger**' in line:
                        cliffhanger = line.split('**Cliffhanger**')[-1].strip(': -')
                    elif line.startswith('- ') and not any(keyword in line for keyword in ['**Key Events**', '**Character**', '**Setting**', '**Cliffhanger**']):
                        # Additional events
                        key_events.append(line[2:])
                
                chapters.append({
                    "chapter_number": chapter_num,
                    "title": title,
                    "key_events": key_events if key_events else ["Plot development continues"],
                    "character_development": character_development or "Character growth and development",
                    "setting": setting or "Story setting continues",
                    "cliffhanger": cliffhanger or "Chapter ends with anticipation"
                })
        
        return chapters

    def optimize(self, trainset=None, max_bootstrapped_demos=4, max_labeled_demos=16):
        """Optimize the module using DSPy optimizers."""
        if not trainset:
            trainset = self.examples
            
        if not trainset:
            print("No examples available for optimization")
            return self
            
        # Use only a subset for training if we have many examples
        if len(trainset) > 20:
            trainset = trainset[:20]  # Limit to avoid overfitting
            
        print(f"🔧 Optimizing with {len(trainset)} training examples")
        
        # Use BootstrapFewShot optimizer (no valset parameter)
        optimizer = dspy.BootstrapFewShot(
            metric=metric_function,
            max_bootstrapped_demos=max_bootstrapped_demos,
            max_labeled_demos=max_labeled_demos
        )
        
        try:
            # Optimize the module - BootstrapFewShot only takes trainset
            print("⏳ Running optimization...")
            optimized_module = optimizer.compile(self, trainset=trainset)
            optimized_module.is_optimized = True
            print("✅ Module optimization completed!")
            return optimized_module
            
        except Exception as e:
            print(f"❌ Optimization failed: {e}")
            print("Continuing with non-optimized version...")
            return self

def generate_book_outline_json(idea: str, use_optimized=True, save_result=False, include_chapters=True) -> Dict[str, Any]:
    """
    Generate a cinematic story summary with a hook using CoT and DSPy.
    
    Args:
        idea: The story idea to generate from
        use_optimized: Whether to use the optimized version (if available)
        save_result: Whether to save the result as a new training example
        include_chapters: Whether to include chapter-by-chapter breakdown
    
    Returns:
        Dict with 'summary', 'genre', 'tone', 'book_title', 'reflection', and 'chapter_breakdown'
    """
    if not idea or not idea.strip():
        return {
            "success": False,
            "summary": "Please provide a story idea to generate an outline.",
            "genre": "Unknown",
            "tone": "Unknown",
            "book_title": "Untitled Story",
            "reflection": "No input provided",
            "chapters": [],
            "error": "No input provided"
        }
    
    try:
        # Get optimized generator (cached, only optimizes when needed)
        if use_optimized:
            generator = get_optimized_generator()
        else:
            generator = OutlineGenerator()
        
        # Generate the story
        result = generator(idea=idea.strip(), include_chapters=include_chapters)
        
        # Convert DSPy Prediction to dict
        output = {
            "success": True,
            "summary": result.summary,
            "genre": result.genre,
            "tone": result.tone,
            "book_title": result.book_title,  # Now included!
            "reflection": result.reflection,
            "chapters": result.chapter_breakdown,  # Now structured as JSON array
            "is_optimized": generator.is_optimized,
            "outline_json": {
                "book_title": result.book_title,
                "summary": result.summary,
                "genre": result.genre,
                "tone": result.tone,
                "chapters": result.chapter_breakdown,
                "main_characters": result.main_characters,  # NEW: Characters from LLM
                "key_locations": result.key_locations,       # NEW: Locations from LLM
                "theme": result.tone,   # Use tone as theme for now
                "style": result.genre,  # Use genre as style for now
                "language": "English",
                "tags": [result.genre.lower()],
                "estimated_total_chapters": len(result.chapter_breakdown) if result.chapter_breakdown else 12
            }
        }
        
        # Save as new example if requested (include book_title in training data)
        if save_result and result.summary and len(result.summary.strip()) > 50:
            save_new_example(
                idea.strip(), 
                result.summary, 
                result.genre, 
                result.tone, 
                result.book_title
            )
            # Force re-optimization next time since we have new data
            global _optimized_generator
            _optimized_generator = None
        
        return output
        
    except Exception as e:
        return {
            "success": False,
            "summary": f"Failed to generate outline: {str(e)}",
            "genre": "Unknown", 
            "tone": "Unknown",
            "book_title": "Untitled Story",
            "reflection": "Generation failed",
            "chapters": [],
            "is_optimized": False,
            "error": str(e),
            "outline_json": {
                "book_title": "Untitled Story",
                "summary": f"Failed to generate outline: {str(e)}",
                "genre": "Unknown",
                "tone": "Unknown",
                "chapters": [],
                "main_characters": [],  # Empty array for error case
                "key_locations": [],    # Empty array for error case
                "theme": "Unknown",
                "style": "Unknown",
                "language": "English",
                "tags": [],
                "estimated_total_chapters": 12
            }
        }

def format_json_to_display_text(outline_json: Dict[str, Any]) -> str:
    """
    Convert JSON outline to formatted text for display.
    This function formats the outline for user-friendly display.
    """
    try:
        book_title = outline_json.get("book_title", "Untitled Story")
        summary = outline_json.get("summary", "")
        genre = outline_json.get("genre", "Unknown")
        tone = outline_json.get("tone", "Unknown")
        chapters = outline_json.get("chapters", [])
        
        formatted_text = f"""📚 **{book_title}**

**Genre:** {genre}
**Tone:** {tone}

**Story Summary:**
{summary}

**Chapter Breakdown:**
"""
        
        for i, chapter in enumerate(chapters, 1):
            chapter_title = chapter.get("title", f"Chapter {i}")
            key_events = chapter.get("key_events", [])
            
            formatted_text += f"\n**Chapter {i}: {chapter_title}**\n"
            
            if key_events:
                for event in key_events[:3]:  # Show first 3 events
                    formatted_text += f"• {event}\n"
            
            cliffhanger = chapter.get("cliffhanger", "")
            if cliffhanger:
                formatted_text += f"*Ends with: {cliffhanger}*\n"
        
        return formatted_text
        
    except Exception as e:
        return f"Error formatting outline: {str(e)}"

def generate_specific_chapter(chapter_breakdown: list, chapter_number: int, writing_style: str = "engaging", word_count: int = 2000) -> str:
    """
    Generate a specific chapter based on the structured chapter breakdown.
    
    Args:
        chapter_breakdown: List of structured chapter objects
        chapter_number: Which chapter to generate (1-based)
        writing_style: Style of writing (engaging, descriptive, fast-paced, etc.)
        word_count: Target word count for the chapter
    
    Returns:
        The generated chapter content
    """
    
    if not chapter_breakdown or chapter_number < 1 or chapter_number > len(chapter_breakdown):
        return f"Error: Chapter {chapter_number} not found in breakdown"
    
    # Get the specific chapter info (convert to 0-based index)
    chapter_info = chapter_breakdown[chapter_number - 1]
    
    chapter_prompt = f"""
    You are a professional novelist writing a specific chapter of a story.
    
    Write Chapter {chapter_number}: "{chapter_info.get('title', f'Chapter {chapter_number}')}"
    
    Chapter Structure:
    - Key Events: {', '.join(chapter_info.get('key_events', []))}
    - Character Development: {chapter_info.get('character_development', '')}
    - Setting: {chapter_info.get('setting', '')}
    - End with: {chapter_info.get('cliffhanger', '')}
    
    Write in an {writing_style} style with approximately {word_count} words.
    
    Guidelines:
    - Follow the plot points and character development outlined above
    - Include vivid descriptions and dialogue
    - Maintain consistency with the story's tone and genre
    - End with the specified cliffhanger or transition
    - Show don't tell - use scenes and action rather than summary
    - Include sensory details and emotional depth
    
    Write the complete chapter now:
    """
    
    try:
        # Use the same LM instance
        chapter_content = lm(chapter_prompt)[0].generations[0].text.strip()
        return chapter_content
    except Exception as e:
        return f"Error generating chapter {chapter_number}: {str(e)}"

def train_from_user_feedback(idea: str, good_summary: str, genre: str, tone: str, book_title: str = None):
    """
    Add user feedback as a training example and re-optimize the model.
    Call this when user provides a good example or corrects a bad one.
    """
    save_new_example(idea, good_summary, genre, tone, book_title)
    
    # Force re-optimization next time since we have new training data
    global _optimized_generator
    _optimized_generator = None
    print("🔄 New training data added. Will re-optimize on next request.")
    
    return True

def force_reoptimization():
    """Force immediate re-optimization with current examples."""
    generator = get_optimized_generator(force_reoptimize=True)
    return generator

class RewriteTextSignature(dspy.Signature):
    """You are an expert editor and writing coach specializing in improving narrative text.
    
    Your task is to rewrite the given text to improve clarity, flow, engagement, and emotional impact.
    
    Consider the story context provided (genre, characters, setting) to ensure the rewrite fits seamlessly.
    
    Improvements to focus on:
    1. Clarity and conciseness
    2. Emotional depth and engagement
    3. Better word choice and sentence flow
    4. Maintaining the author's voice and style
    5. Genre-appropriate tone and atmosphere
    
    Keep the same length approximately, and maintain the core meaning and plot points."""
    
    original_text = dspy.InputField(desc="The original text to be rewritten")
    story_context = dspy.InputField(desc="Story context including title, genre, characters, and setting")
    analysis = dspy.OutputField(desc="Brief analysis of what needs improvement in the original text")
    rewritten_text = dspy.OutputField(desc="The improved, rewritten version of the text")

class RewriteTextModule(dspy.Module):
    """Module for rewriting text with context awareness."""
    
    def __init__(self):
        super().__init__()
        self.rewrite = dspy.ChainOfThought(RewriteTextSignature)
    
    def forward(self, original_text: str, story_context: Dict[str, Any]):
        # Format context for the AI
        context_str = f"""
        Story Title: {story_context.get('story_title', 'Unknown')}
        Genre: {story_context.get('story_genre', 'Unknown')}
        Current Chapter: {story_context.get('current_chapter', 'Unknown')}
        Story Summary: {story_context.get('story_outline', 'No summary available')}
        """.strip()
        
        return self.rewrite(
            original_text=original_text,
            story_context=context_str
        )

def rewrite_text_with_context(original_text: str, story_context: Dict[str, Any] = None) -> str:
    """
    Style-preserving rewrite: improve clarity, flow, and correctness WITHOUT changing meaning.

    We intentionally avoid supplying large story context here to prevent the model from
    introducing or removing narrative details. The only accepted input is the selected text,
    with strict rewrite constraints.

    Args:
        original_text: The passage selected by the user
        story_context: Ignored except for optional tiny hints (tone/level) if provided

    Returns:
        The rewritten passage, or the original text on failure
    """
    try:
        logger.info(f"[REWRITE_FUNCTION] Style-preserving rewrite for {len(original_text)} chars")

        # Optional lightweight hints
        tone = (story_context or {}).get("tone") if isinstance(story_context, dict) else None
        reading_level = (story_context or {}).get("reading_level") if isinstance(story_context, dict) else None

        # Build a strict, self-contained prompt
        constraints = [
            "Preserve the exact meaning, facts, and implications.",
            "Do not add new information or remove details.",
            "Maintain the original point of view and verb tense.",
            "Keep names and terms exactly as written.",
            "Keep the length within ±10% of the original.",
            "Improve grammar, punctuation, clarity, and rhythm.",
            "Output only the rewritten passage with no commentary.",
        ]
        if tone:
            constraints.insert(0, f"Target tone: {tone}.")
        if reading_level:
            constraints.insert(1, f"Target reading level: {reading_level}.")

        system_prompt = (
            "You are a careful line editor. You polish prose while strictly preserving meaning."
        )
        user_prompt = (
            "Rewrite the passage to improve clarity, flow, and style while preserving its exact meaning.\n"
            + "\n".join(f"- {c}" for c in constraints)
            + "\n\nPassage:\n" + original_text
        )

        # Use OpenAI chat model directly to avoid the broader DSPy chain-of-thought for this task
        from langchain_openai import ChatOpenAI
        llm = ChatOpenAI(model=settings.OPENAI_MODEL, openai_api_key=settings.OPENAI_API_KEY)
        response = llm.invoke([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ])
        rewritten = (response.content or "").strip()
        if not rewritten:
            logger.warning("[REWRITE_FUNCTION] Empty response; returning original text")
            return original_text
        return rewritten

    except Exception as e:
        logger.error(f"[REWRITE_FUNCTION] Error during rewrite: {e}")
        return original_text