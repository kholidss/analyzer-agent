from transformers import Trainer, TrainingArguments, GPT2LMHeadModel, GPT2Tokenizer

class FineTuningTrainer:
    def __init__(self, model_name="gpt2"):
        self.tokenizer = GPT2Tokenizer.from_pretrained(model_name)
        self.model = GPT2LMHeadModel.from_pretrained(model_name)

    def fine_tune(self, dataset):
        # Tokenize dataset
        inputs = [entry['cv_text'] + "\n" + entry['skills_required'] + "\n" + entry['education_location'] for entry in dataset]
        encodings = self.tokenizer(inputs, truncation=True, padding=True, return_tensors="pt")

        labels = [entry['is_suitable'] for entry in dataset]

        training_args = TrainingArguments(
            output_dir='./results',
            evaluation_strategy="epoch",
            learning_rate=5e-5,
            per_device_train_batch_size=4,
            num_train_epochs=3,
        )

        # Initialize Trainer
        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=encodings,
            eval_dataset=encodings
        )

        trainer.train()