from typing import Text

import pytest

from rasa.validator import Validator
from rasa.shared.importers.rasa import RasaFileImporter
from rasa.shared.importers.autoconfig import TrainingType
from pathlib import Path


async def test_verify_intents_does_not_fail_on_valid_data(nlu_data_path: Text):
    importer = RasaFileImporter(
        domain_path="data/test_moodbot/domain.yml", training_data_paths=[nlu_data_path],
    )
    validator = await Validator.from_importer(importer)
    assert validator.verify_intents()


async def test_verify_intents_does_fail_on_invalid_data(nlu_data_path: Text):
    # domain and nlu data are from different domain and should produce warnings
    importer = RasaFileImporter(
        domain_path="data/test_domains/default.yml",
        training_data_paths=[nlu_data_path],
    )
    validator = await Validator.from_importer(importer)
    assert not validator.verify_intents()


async def test_verify_valid_responses():
    importer = RasaFileImporter(
        domain_path="data/test_domains/selectors.yml",
        training_data_paths=[
            "data/test_selectors/nlu.yml",
            "data/test_selectors/stories.yml",
        ],
    )
    validator = await Validator.from_importer(importer)
    assert validator.verify_utterances_in_stories()


async def test_verify_valid_responses_in_rules(nlu_data_path: Text):
    importer = RasaFileImporter(
        domain_path="data/test_domains/default.yml",
        training_data_paths=[
            nlu_data_path,
            "data/test_yaml_stories/rules_without_stories_and_wrong_names.yml",
        ],
    )
    validator = await Validator.from_importer(importer)
    assert not validator.verify_utterances_in_stories()


async def test_verify_story_structure(stories_path: Text):
    importer = RasaFileImporter(
        domain_path="data/test_domains/default.yml", training_data_paths=[stories_path],
    )
    validator = await Validator.from_importer(importer)
    assert validator.verify_story_structure(ignore_warnings=False)


async def test_verify_bad_story_structure():
    importer = RasaFileImporter(
        domain_path="data/test_domains/default.yml",
        training_data_paths=["data/test_yaml_stories/stories_conflicting_2.yml"],
    )
    validator = await Validator.from_importer(importer)
    assert not validator.verify_story_structure(ignore_warnings=False)


async def test_verify_bad_e2e_story_structure_when_text_identical(tmp_path: Path):
    story_file_name = tmp_path / "stories.yml"
    story_file_name.write_text(
        """
        version: "2.0"
        stories:
        - story: path 1
          steps:
          - user: |
              amazing!
          - action: utter_happy
        - story: path 2 (should always conflict path 1)
          steps:
          - user: |
              amazing!
          - action: utter_cheer_up
        """
    )
    # The two stories with identical user texts
    importer = RasaFileImporter(
        config_file="data/test_config/config_defaults.yml",
        domain_path="data/test_domains/default.yml",
        training_data_paths=[story_file_name],
        training_type=TrainingType.NLU,
    )
    validator = await Validator.from_importer(importer)
    assert not validator.verify_story_structure(ignore_warnings=False)


async def test_verify_bad_e2e_story_structure_when_text_differs_by_whitespace(
    tmp_path: Path,
):
    story_file_name = tmp_path / "stories.yml"
    story_file_name.write_text(
        """
        version: "2.0"
        stories:
        - story: path 1
          steps:
          - user: |
              truly amazing!
          - action: utter_happy
        - story: path 2 (should always conflict path 1)
          steps:
          - user: |
              truly  amazing!
          - action: utter_cheer_up
        """
    )
    importer = RasaFileImporter(
        config_file="data/test_config/config_defaults.yml",
        domain_path="data/test_domains/default.yml",
        training_data_paths=[story_file_name],
        training_type=TrainingType.NLU,
    )
    validator = await Validator.from_importer(importer)
    assert not validator.verify_story_structure(ignore_warnings=False)


async def test_verify_correct_e2e_story_structure(tmp_path: Path):
    story_file_name = tmp_path / "stories.yml"
    with open(story_file_name, "w") as file:
        file.write(
            """
            stories:
            - story: path 1
              steps:
              - user: |
                  hello assistant! Can you help me today?
              - action: utter_greet
            - story: path 2 - state is similar but different from the one in path 1
              steps:
              - user: |
                  hello assistant! you Can help me today?
              - action: utter_goodbye
            - story: path 3
              steps:
              - user: |
                  That's it for today. Chat again tomorrow!
              - action: utter_goodbye
            """
        )
    importer = RasaFileImporter(
        config_file="data/test_config/config_defaults.yml",
        domain_path="data/test_domains/default.yml",
        training_data_paths=[story_file_name],
        training_type=TrainingType.NLU,
    )
    validator = await Validator.from_importer(importer)
    assert validator.verify_story_structure(ignore_warnings=False)


async def test_verify_correct_e2e_story_structure_with_intents(tmp_path: Path):
    story_file_name = tmp_path / "stories.yml"
    with open(story_file_name, "w") as file:
        file.write(
            """
            stories:
            - story: path 1
              steps:
              - intent: greet
              - action: utter_greet
            - story: path 2
              steps:
              - intent: goodbye
              - action: utter_goodbye
            """
        )
    importer = RasaFileImporter(
        config_file="data/test_config/config_defaults.yml",
        domain_path="data/test_domains/default.yml",
        training_data_paths=[story_file_name],
        training_type=TrainingType.NLU,
    )
    validator = await Validator.from_importer(importer)
    assert validator.verify_story_structure(ignore_warnings=False)


async def test_verify_story_structure_ignores_rules():
    importer = RasaFileImporter(
        domain_path="data/test_domains/default.yml",
        training_data_paths=[
            "data/test_yaml_stories/stories_with_rules_conflicting.yml"
        ],
    )
    validator = await Validator.from_importer(importer)
    assert validator.verify_story_structure(ignore_warnings=False)


async def test_verify_bad_story_structure_ignore_warnings():
    importer = RasaFileImporter(
        domain_path="data/test_domains/default.yml",
        training_data_paths=["data/test_yaml_stories/stories_conflicting_2.yml"],
    )
    validator = await Validator.from_importer(importer)
    assert validator.verify_story_structure(ignore_warnings=True)


async def test_verify_there_is_example_repetition_in_intents(nlu_data_path: Text):
    # moodbot nlu data already has duplicated example 'good afternoon'
    # for intents greet and goodbye
    importer = RasaFileImporter(
        domain_path="data/test_moodbot/domain.yml", training_data_paths=[nlu_data_path],
    )
    validator = await Validator.from_importer(importer)
    assert not validator.verify_example_repetition_in_intents(False)


async def test_verify_logging_message_for_repetition_in_intents(
    caplog, nlu_data_path: Text
):
    # moodbot nlu data already has duplicated example 'good afternoon'
    # for intents greet and goodbye
    importer = RasaFileImporter(
        domain_path="data/test_moodbot/domain.yml", training_data_paths=[nlu_data_path],
    )
    validator = await Validator.from_importer(importer)
    caplog.clear()  # clear caplog to avoid counting earlier debug messages
    with pytest.warns(UserWarning) as record:
        validator.verify_example_repetition_in_intents(False)
    assert len(record) == 1
    assert "You should fix that conflict " in record[0].message.args[0]


async def test_early_exit_on_invalid_domain():
    domain_path = "data/test_domains/duplicate_intents.yml"

    importer = RasaFileImporter(domain_path=domain_path)
    with pytest.warns(UserWarning) as record:
        validator = await Validator.from_importer(importer)
    validator.verify_domain_validity()

    # two for non-unique domains
    assert len(record) == 2
    assert (
        f"Loading domain from '{domain_path}' failed. Using empty domain. "
        "Error: 'Intents are not unique! Found multiple intents with name(s) "
        "['default', 'goodbye']. Either rename or remove the duplicate ones.'"
        in record[0].message.args[0]
    )
    assert record[0].message.args[0] == record[1].message.args[0]


async def test_verify_there_is_not_example_repetition_in_intents():
    importer = RasaFileImporter(
        domain_path="data/test_moodbot/domain.yml",
        training_data_paths=["examples/knowledgebasebot/data/nlu.md"],
    )
    validator = await Validator.from_importer(importer)
    assert validator.verify_example_repetition_in_intents(False)


async def test_response_selector_responses_in_domain_no_errors():
    importer = RasaFileImporter(
        config_file="data/test_config/config_defaults.yml",
        domain_path="data/test_domains/response_selector_responses_in_domain.yml",
        training_data_paths=[
            "data/test_yaml_stories/test_base_retrieval_intent_story.yml"
        ],
        training_type=TrainingType.CORE,
    )
    validator = await Validator.from_importer(importer)
    assert validator.verify_utterances_in_stories(ignore_warnings=True)


async def test_invalid_domain_mapping_policy():
    importer = RasaFileImporter(
        domain_path="data/test_domains/default_with_mapping.yml"
    )
    validator = await Validator.from_importer(importer)
    assert validator.verify_domain_validity() is False
