import xlsxwriter
import heatmap_data

VRM_RANGE = 1 + 27 + 3

def get_cell_value(sheet_name2, column_number, row_number):
    if row_number > 26 or row_number == 0:
        return 0
    else:
        return heatmap_data.heatmap_array[sheet_name2][row_number][column_number]


# 3D data is stored in a excel spreadsheet format in a 3D array,
# hence some math is needed to convert between them
def xz_to_col(X, Z):
    return X + (7 * Z)


def y_to_row(Y):
    return VRM_RANGE - 1 - 3 - Y


# defining the different heatmap sheets
stems, shroomlight, vrm0, vrm1, vrm2, vrm3 = 0, 1, 2, 3, 4, 5

outSheet = []
outWorkbook = xlsxwriter.Workbook(r"VRM_Optimisation_Heatmap2.xlsx")
print(VRM_RANGE)
outSheet.append(outWorkbook.add_worksheet(f"vrm_optimisation_values"))
outSheet.append(outWorkbook.add_worksheet(f"vrm_raw_added_values"))
outSheet.append(outWorkbook.add_worksheet(f"vrm0_raw_values"))

for y in range(VRM_RANGE):
    for x in range(7):
        for z in range(7):
            # finding the avg wart blocks generated at the block which the pre-placed vrm wart block obstructs
            vrm0_value = get_cell_value(vrm0, xz_to_col(x, z), y_to_row(y))

            # calculating avg wart blocks generated for the 3 above adjacent blocks with vrm
            vrm_above_value = (
                    get_cell_value(vrm1, xz_to_col(x, z), y_to_row(y + 1)) +
                    get_cell_value(vrm2, xz_to_col(x, z), y_to_row(y + 2)) +
                    get_cell_value(vrm3, xz_to_col(x, z), y_to_row(y + 3))
            )
            # calculating avg wart blocks generated for the 3 above adjacent blocks without vrm
            no_vrm_above_value = (
                    get_cell_value(vrm0, xz_to_col(x, z), y_to_row(y + 1)) +
                    get_cell_value(vrm0, xz_to_col(x, z), y_to_row(y + 2)) +
                    get_cell_value(vrm0, xz_to_col(x, z), y_to_row(y + 3))
            )

            # calculating the added wart blocks that the pre-placed wart block produces through vrm
            added_vrm_value = vrm_above_value - no_vrm_above_value - vrm0_value
            # vrm added value
            outSheet[0].write(y_to_row(y), xz_to_col(x, z), added_vrm_value)
            # vrm raw value
            outSheet[1].write(y_to_row(y), xz_to_col(x, z), vrm_above_value - no_vrm_above_value)
            # vrm0 raw value
            outSheet[2].write(y_to_row(y), xz_to_col(x, z), vrm0_value)

outWorkbook.close()
