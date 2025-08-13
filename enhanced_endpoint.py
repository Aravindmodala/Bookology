# ENHANCED Generate and Save Chapter Endpoint
# This replaces the old endpoint with full DNA + Vector support

@app.post("/generate_and_save_chapter")
async def generate_and_save_chapter_endpoint(
    chapter_input: GenerateNextChapterInput,
    background_tasks: BackgroundTasks,
    user = Depends(get_authenticated_user)
):
    '''
    ENHANCED: Generate and save chapter with DNA, summaries, and vector embeddings.
    Now uses the optimized service for complete feature support.
    '''
    try:
        logger.info(f' ENHANCED GENERATE & SAVE: Starting Chapter {chapter_input.chapter_number} for story {chapter_input.story_id}...')
        
        # Verify story belongs to user
        story_response = supabase.table('Stories').select('*').eq('id', chapter_input.story_id).eq('user_id', user.id).execute()
        if not story_response.data:
            raise HTTPException(status_code=404, detail='Story not found or access denied')
        
        story = story_response.data[0]
        story_title = story.get('story_title', 'Untitled Story')
        story_outline = story.get('story_outline', chapter_input.story_outline)
        
        # STEP 1: Generate chapter using enhanced generator
        from services.enhanced_chapter_generator import enhanced_chapter_generator
        
        # Get previous chapters for context (with DNA and summaries)
        previous_chapters_response = supabase.table('Chapters').select(
            'content, summary, dna, chapter_number, title'
        ).eq('story_id', chapter_input.story_id).eq('is_active', True).lt(
            'chapter_number', chapter_input.chapter_number
        ).order('chapter_number').execute()
        
        previous_chapters = previous_chapters_response.data if previous_chapters_response.data else []
        
        logger.info(f' Using {len(previous_chapters)} previous chapters for enhanced generation')
        
        # Generate chapter with enhanced context (DNA + summaries + vectors)
        generation_result = await enhanced_chapter_generator.generate_next_chapter_enhanced(
            story_id=chapter_input.story_id,
            story_title=story_title,
            story_outline=story_outline,
            current_chapter_number=chapter_input.chapter_number,
            user_choice='',  # No specific user choice for initial generation
            previous_chapters=previous_chapters,
            choice_options=[]
        )
        
        logger.info(f' STEP 1 COMPLETE: Enhanced chapter generated!')
        logger.info(f' Content: {len(generation_result["content"])} chars')
        logger.info(f' DNA: {"generated" if generation_result.get("dna") else "none"}')
        logger.info(f' Summary: {"generated" if generation_result.get("summary") else "none"}')
        
        # STEP 2: Save using optimized service (DNA + summaries + vectors)
        from app.services.fixed_optimized_chapter_service import fixed_optimized_chapter_service
        
        # Prepare chapter data for optimized save
        chapter_dict = {
            'story_id': chapter_input.story_id,
            'chapter_number': chapter_input.chapter_number,
            'content': generation_result['content'],
            'title': generation_result.get('title', f'Chapter {chapter_input.chapter_number}'),
            'choices': generation_result.get('choices', []),
            'user_choice': ''
        }
        
        # Save with full optimization (DNA + summaries + vectors)
        save_result = await fixed_optimized_chapter_service.save_chapter_optimized(
            chapter_data=chapter_dict,
            user_id=user.id,
            supabase_client=supabase
        )
        
        logger.info(f' STEP 2 COMPLETE: Chapter saved with optimization!')
        logger.info(f' Total save time: {save_result.save_time:.2f}s')
        logger.info(f' Vector chunks: {save_result.vector_chunks}')
        
        # STEP 3: Update story current chapter
        try:
            supabase.table('Stories').update({
                'current_chapter': chapter_input.chapter_number
            }).eq('id', chapter_input.story_id).execute()
            logger.info(f' Updated story current_chapter to {chapter_input.chapter_number}')
        except Exception as update_error:
            logger.warning(f' Could not update story current_chapter: {update_error}')
        
        return {
            'success': True,
            'message': f'Chapter {chapter_input.chapter_number} generated and saved with full optimization!',
            'chapter_id': save_result.chapter_id,
            'story_id': chapter_input.story_id,
            'chapter_number': chapter_input.chapter_number,
            'chapter_content': generation_result['content'],
            'title': generation_result.get('title'),
            'summary': save_result.summary,
            'choices': save_result.choices,
            'enhanced_features': {
                'dna_extracted': bool(generation_result.get('dna')),
                'summary_generated': bool(save_result.summary),
                'vector_chunks_created': save_result.vector_chunks,
                'async_pipeline': True,
                'background_processing': True
            },
            'performance_metrics': {
                'generation_time': generation_result['metrics']['generation_time'],
                'save_time': save_result.save_time,
                'total_time': generation_result['metrics']['generation_time'] + save_result.save_time,
                **save_result.performance_metrics
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f' Error in enhanced generate & save: {str(e)}')
        import traceback
        logger.error(f' Traceback: {traceback.format_exc()}')
        raise HTTPException(status_code=500, detail=f'Failed to generate and save chapter: {str(e)}')
