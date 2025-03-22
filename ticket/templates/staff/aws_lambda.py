# The following code is provided only as a reference. It is used directly in AWS. Our codebase needs only to interact with the AWS API.
# I have included it here for marking purposes.

import json
import boto3
import os

def get_from_s3(bucket_name, file_key):
    """Get context from S3"""
    s3 = boto3.client('s3')
    try:
        print(f"Attempting to read from S3: {bucket_name}/{file_key}")
        response = s3.get_object(Bucket=bucket_name, Key=file_key)
        content = response['Body'].read().decode('utf-8')
        print(f"Successfully read {len(content)} bytes from S3")
        return content
    except Exception as e:
        print(f"Error reading from S3: {str(e)}")
        return ""

def construct_prompt(event, context_text):
    """Construct prompt based on action type"""
    print("Constructing prompt with event data and context")
    ticket_context = f"""Ticket #{event['ticket_id']}
Student: {event['student_name']}
Program: {event['student_program']}
Year: {event['student_year']}
Department: {event['department']}

Your Name: {event['staff_name']}
Your Department Name: {event['staff_department']}

Subject: {event['subject']}
Description: {event['description']}

Previous Messages:
{chr(10).join([f"{msg['author']}: {msg['content']}" for msg in event['messages']])}

Department Context:
{context_text}"""

    if event['action'] == 'refine_ai':
        print("Creating refine_ai prompt")
        prompt = f"""Human: Please refine this response to be more professional and polished while keeping its core message and tone:

{event['current_text']}

Context (for reference):
{ticket_context}"""
    else:  # generate_ai
        print("Creating generate_ai prompt")
        prompt = f"""Human: Please generate a professional and helpful response to this ticket:

{ticket_context}"""

    print(f"Final prompt length: {len(prompt)} characters")
    return prompt

def call_bedrock(prompt):
    """Call Bedrock/Claude"""
    print("Initializing Bedrock client")
    bedrock = boto3.client(
        service_name='bedrock-runtime',
        region_name='eu-west-2'
    )
    
    print("Constructing Bedrock request body")
    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 300,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }
        ]
    })

    try:
        print("Calling Bedrock invoke_model")
        response = bedrock.invoke_model(
            modelId="anthropic.claude-3-haiku-20240307-v1:0",
            contentType="application/json",
            accept="application/json",
            body=body
        )
        
        print("Parsing Bedrock response")
        response_body = json.loads(response.get('body').read())
        print(f"Raw Bedrock response: {json.dumps(response_body)}")
        
        response_text = response_body.get('content', [{'text': ''}])[0]['text']
        print(f"Extracted response text length: {len(response_text)}")
        return response_text
    except Exception as e:
        print(f"Error calling Bedrock: {str(e)}")
        raise  # Re-raise to be handled by main handler

def lambda_handler(event, context):
    """Main Lambda handler"""
    try:
        print(f"Lambda received event: {json.dumps(event)}")
        
        # Get department context from S3
        department = event.get('department', '').lower()
        if not department:
            raise ValueError("Department is required")
            
        context_file = f"departments/{department}.rtf"  # Using .rtf extension
        print(f"Getting context for department: {department}")
        context_text = get_from_s3('university-ticketing', context_file)
        
        if not context_text:
            print(f"Warning: No context found for department {department}")
        
        # Construct prompt with context
        print("Constructing prompt")
        prompt = construct_prompt(event, context_text)
        
        # Call Bedrock/Claude
        print("Calling Bedrock")
        response = call_bedrock(prompt)
        
        print(f"Returning success response with text length: {len(response)}")
        return {
            "statusCode": 200,
            "body": json.dumps({
                "success": True,
                "response": response
            })
        }
    except Exception as e:
        print(f"Lambda handler error: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({
                "success": False,
                "error": str(e)
            })
        }