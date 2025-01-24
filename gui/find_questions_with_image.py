# extract_images.py
import json
import re
import os

def extract_questions_with_images(input_file):
    """
    Extracts questions containing image descriptions from the input JSON file.
    """
    # Read input JSON file
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Initialize result structure
    result = {
        "choiceQuestions": [],
        "trueFalseQuestions": [],
        "shortQuestions": []
    }
    
    # Regular expression to match image descriptions
    img_pattern = r'\[Mô tả ảnh:.*?\]'
    
    # Process each question type
    for question_type in ["choiceQuestions", "trueFalseQuestions", "shortQuestions"]:
        if question_type in data:
            for question_group in data[question_type]:
                question_number = question_group["questionNumber"]
                filtered_list = []
                
                for i, question in enumerate(question_group["list"]):
                    if re.search(img_pattern, question["content"]):
                        # Add question index for accurate updating
                        question["_index"] = i
                        filtered_list.append(question)
                
                if filtered_list:
                    result[question_type].append({
                        "questionNumber": question_number,
                        "list": filtered_list
                    })
    
    # Remove empty question types
    result = {k: v for k, v in result.items() if v}
    
    # Construct output file path in the same directory
    output_dir = os.path.dirname(input_file) # Lấy thư mục chứa file đầu vào
    output_file = os.path.join(output_dir, 'questions_with_images.json') # Kết hợp đường dẫn thư mục và tên file đầu ra
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    return output_file

# update_images.py
# update_images.py
def update_questions_with_images(original_file, images_file):
    """
    Updates the original JSON file with questions containing images from the images file, modifying the original file.
    """
    # Read both JSON files
    with open(original_file, 'r', encoding='utf-8') as f:
        original_data = json.load(f)
    
    with open(images_file, 'r', encoding='utf-8') as f:
        images_data = json.load(f)
    
    # Update original data
    for question_type in images_data:
        for image_group in images_data[question_type]:
            question_number = image_group["questionNumber"]
            
            # Find matching question group in original data
            for orig_group in original_data[question_type]:
                if orig_group["questionNumber"] == question_number:
                    # Update each question in the group
                    for image_question in image_group["list"]:
                        index = image_question.pop('_index', None)  # Remove _index before updating
                        if index is not None:
                            orig_group["list"][index] = image_question
                    break
    
    # Save updated data to the original file
    with open(original_file, 'w', encoding='utf-8') as f:
        json.dump(original_data, f, ensure_ascii=False, indent=2)
    
    return original_file

def validate_update(original_file, updated_file):
    """
    Validates that the update was performed correctly by comparing the files.
    """
    with open(original_file, 'r', encoding='utf-8') as f:
        original_data = json.load(f)
    
    with open(updated_file, 'r', encoding='utf-8') as f:
        updated_data = json.load(f)
        
    differences = []
    
    # Check structure remains the same
    for question_type in original_data:
        if question_type not in updated_data:
            differences.append(f"Missing question type: {question_type}")
            continue
            
        for orig_group, updated_group in zip(original_data[question_type], updated_data[question_type]):
            if orig_group["questionNumber"] != updated_group["questionNumber"]:
                differences.append(f"Question number mismatch in {question_type}")
                
            if len(orig_group["list"]) != len(updated_group["list"]):
                differences.append(f"Question list length changed in {question_type}, number {orig_group['questionNumber']}")
    
    return differences

# Example usage
if __name__ == "__main__":
    input_file = "E:\Edmicro\Đề GK2 Toán 10_full lời giải - (test)_gemini_output.json"
    
    # Extract questions with images
    images_file = extract_questions_with_images(input_file)
    images_file = "E:\Edmicro\questions_with_images.json"
    print(f"Questions with images extracted to: {images_file}")
    
#     # Update original file with image questions
#     output_file = update_questions_with_images(input_file, images_file)
#     print(f"Updated questions saved to: {output_file}")
    
#     # Validate the update
#     differences = validate_update(input_file, output_file)
#     if differences:
#         print("Validation found issues:")
#         for diff in differences:
#             print(f"- {diff}")
#     else:
#         print("Update validated successfully")