from fastapi import FastAPI, Path, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, computed_field
from typing import Annotated, Literal, Optional
import json

app = FastAPI()

# Pydantic Model
class Patient(BaseModel):

    id: Annotated[str, Field(..., description = "ID of the patient", examples = ["P001"])]
    
    name: Annotated[str, Field(..., description = "Name of the patient")]

    city: Annotated[str, Field(..., description = "city where the patient is living")]
    
    age: Annotated[int, Field(..., gt = 0, lt = 120, description = "Age of the patient")]
    
    gender: Annotated[Literal['Male', 'Female', 'Others'], Field(..., description = "Gender of the patient")]
    
    height: Annotated[float, Field(..., gt = 0, description = "Height of the patient in metres(M)")]
    
    weight: Annotated[float, Field(..., gt = 0, description = "Weight of the patient in kilograms(KG)")]

    @computed_field
    @property
    def bmi(self) -> float:
        bmi =round(self.weight/ (self.height**2), 2) 
        return bmi

    @computed_field
    @property
    def verdict(self) -> str:
        if self.bmi < 18.5:
            return "Underweight"
        elif self.bmi < 25:
            return "Normal"
        elif self.bmi < 30:
            return "Normal"
        else:
            return "Overweight"

class PatientUpdate(BaseModel):
    
    name: Annotated[Optional[str], Field(default = None)]

    city: Annotated[Optional[str], Field(default = None)]

    age: Annotated[Optional[int], Field(default = None, gt = 0)]

    gender: Annotated[Optional[Literal['Male', 'Female','Others']], Field(default = None)]

    height: Annotated[Optional[float], Field(default = None, gt = 0)]

    weight: Annotated[Optional[float], Field(default = None, gt = 0)]

def load_data():
    with open('patients.json', 'r') as f:
        data = json.load(f)

    return data

def save_data(data):
    with open("patients.json", "w") as f:
        json.dump(data, f)
    

@app.get("/")
def hello():
    return {'message': 'API for Patient Management System'}

@app.get('/about')
def about():
    return {'message': 'This is an API for managing patient records'}

@app.get('/view')
def view():
    data = load_data()
    return data


# Path Parameter
@app.get('/patient/{patient_id}')
def view_patient(patient_id: str = Path(..., description = 'ID of the patient in the DB', 
                                        example = 'P001')):
    data = load_data()

    if patient_id in data:
        return data[patient_id]
    
    raise HTTPException(status_code = 404, detail = "Patient not found")

# Query Parameter
@app.get('/sort')
def sort_patient(sort_by: str = Query(..., description = "Sort on the basis of height, weight or bmi"), 
                 order: str = Query('asc', description = "Sort in asc or desc order")):
    
    valid_fields = ['height', 'weight', 'bmi']

    if sort_by not in valid_fields:
        raise HTTPException(status_code = 400, details = f'Invalid field select from {valid_fields}')

    valid_order = ['asc', 'desc']
    if order not in valid_order:
        raise HTTPException(status_code = 400, details = f'Invalid field select from {valid_order}')
    
    data = load_data()

    sort_order = True if order == 'desc' else False

    sorted_data = sorted(data.values(), key = lambda x: x.get(sort_by, 0), reverse= sort_order)

    return sorted_data

@app.post('/create')
def create_patient(patient: Patient):
    
    # load exisiting data
    data = load_data()

    # check duplicate exists
    if patient.id in data:
        raise HTTPException(status_code = 400, 
                            detail = "Patient already exists")
    
    # new patient add
    data[patient.id] = patient.model_dump(exclude = ["id"])

    # save data into the json file
    save_data(data)

    return JSONResponse(status_code = 201, 
                        content = "Patient created successfully")

@app.put('/edit/{patient_id}')
def update_patient(patient_id: str, patient_update: PatientUpdate):
    
    data = load_data()

    if patient_id not in data:
        raise HTTPException(status_code = 404, detail = "Patient not found")
    
    existing_patient_info = data[patient_id]
    
    updated_patient_info = patient_update.model_dump(exclude_unset = True)

    for key, value in updated_patient_info.items():
        existing_patient_info[key] = value
    
    # existing patient info -> pydantic object -> updated bmi & weight ->
    existing_patient_info['id'] = patient_id
    patient_pydantic_obj = Patient(**existing_patient_info)

    # -> pydantic object -> dict
    existing_patient_info = patient_pydantic_obj.model_dump(exclude = 'id')

    # add this dict to json data
    data[patient_id] = existing_patient_info

    # save data
    save_data(data)

    return JSONResponse(status_code = 200, content = {"message":"patient updated"})

@app.delete('/delete/{patient_id}')
def delete_patient(patient_id: str):

    data = load_data()

    if patient_id not in  data:
        raise HTTPException(status_code = 404, detail = "Patient not found")
    
    del data[patient_id]

    save_data(data)

    return JSONResponse(status_code = 200, content = {"message":"patient deleted"})


    
'''
to run this file run the following command: 
uvicorn main:app --reload

"uvicorn main:app" this part is for running the api endpoint where main is the file name and app is the object of FastAPI
"--reload" whereas this part reloads the server if there is any change made in the api code.

In function headers that have Path and Query the sequence '...' implies that value is required

'''

