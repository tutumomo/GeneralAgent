def main(cache, messages, input, files, output_callback):
    from GeneralAgent.agent import Agent
    from GeneralAgent import skills

    role_prompt = """
You are a video generator, write one piece of code which contains all steps to generate videos according to user requirements.
"""

    functions = [
        skills.create_image,
        # skills.face_restoration,
        skills.stable_video_diffusion,
        skills.concatenate_videos,
        skills.text_to_speech,
        skills.generate_music,
        skills.merge_video_audio
    ]

    agent = cache
    if agent is None:
        agent = Agent.with_functions(functions)
        agent.output_callback = output_callback
        agent.add_role_prompt(role_prompt)
    agent.run(input)
    return agent