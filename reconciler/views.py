import os
from django.shortcuts import render
from django.http import HttpResponse, FileResponse
from reconciler.reconciler import DataReconciler
from django.conf import settings
import logging

def reconcile_view(request):
    context = {}
    if request.method == 'POST':
        try:
            active_roster_file = request.FILES['active_roster_file']
            active_data_file = request.FILES['active_data_file']
            reconciler = DataReconciler(active_roster_file, active_data_file)
            
            reconciler.reconcile()

            zip_file_path = reconciler.save_results(
                zip_file='output.zip',
                active_roster_filename='active_roster_data.xlsx',
                active_data_filename='insurer_active_data.xlsx',
                error_zip_file='error.zip',
                error_roster_filename='error_roster.xlsx',
                error_data_filename='error_data.xlsx'
            )
            context['success_message'] = "Reconciliation Successful!"
            zip_file = open(zip_file_path, 'rb')
            response = FileResponse(zip_file, content_type='application/zip')
            response['Content-Disposition'] = f'attachment; filename="{os.path.basename(zip_file_path)}"'
            return response 
        
        except Exception as e:
            print(f"Error saving results: {str(e)}")
            return HttpResponse(f"An error occurred: {str(e)}", status=500)
    
    return render(request, 'reconcile.html', context)

# def download_template(request, file_path):

#     # Decode the file path by replacing underscores with slashes
#     file_path = file_path.replace('_', '/')
#     # Remove any extra leading/trailing slashes or redundant segments
#     normalized_file_path = os.path.normpath(file_path)
#     # Construct the full file path using settings.BASE_DIR
#     full_file_path = os.path.join(settings.BASE_DIR, normalized_file_path)
    
#     print(f"Constructed file path: {full_file_path}")  # Debugging
    
#     if os.path.exists(full_file_path):
#         with open(full_file_path, 'rb') as file:
#             response = FileResponse(file, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
#             response['Content-Disposition'] = f'attachment; filename="{os.path.basename(full_file_path)}"'
#             return response
#     else:
#         print(f"File not found: {full_file_path}")
#         return HttpResponse("File not found", status=404)

def download_template(request):
    file_path = os.path.join(settings.BASE_DIR, 'reconciler/Template.xlsx')  # Adjust path
    if os.path.exists(file_path):
        response = FileResponse(open(file_path, 'rb'), as_attachment=True, filename='Template.xlsx')
        return response
    else:
        return HttpResponse("File not found.", status=404)


