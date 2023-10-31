import boto3

# Step 1: Configure AWS credentials
aws_access_key_id = 'YOUR_ACCESS_KEY_ID'
aws_secret_access_key = 'YOUR_SECRET_ACCESS_KEY'
aws_region = 'us-east-1'  # Change this to your desired AWS region

# Step 2: Create Boto3 clients for AWS Translate and Polly
translate = boto3.client('translate', region_name=aws_region, aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key)
polly = boto3.client('polly', region_name=aws_region, aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key)

def translate_text(input_text, target_language='en'):
    # Translate the input Chinese text to English
    translation_response = translate.translate_text(
        Text=input_text,
        SourceLanguageCode='auto',  # Auto-detect source language
        TargetLanguageCode=target_language
    )

    translated_text = translation_response['TranslatedText']

    return translated_text

def text_to_mp3(text, output_file):
    # Use Amazon Polly to convert text to MP3
    response = polly.synthesize_speech(
        Text=text,
        OutputFormat='mp3',
        VoiceId='Joanna'  # You can choose a different voice
    )

    # Write the MP3 content to the specified output file
    with open(output_file, 'wb') as f:
        f.write(response['AudioStream'].read())

if __name__ == '__main__':
    input_text = '你好，这是一个示例句子。'  # Replace with your Chinese text
    output_file = 'translated_text.mp3'  # Specify the output MP3 file name

    # Translate the Chinese text to English
    translated_text = translate_text(input_text)

    # Convert the translated text to MP3
    text_to_mp3(translated_text, output_file)

    print(f'Translated text: {translated_text}')
    print(f'MP3 file saved as: {output_file}')

