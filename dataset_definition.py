from ehrql import create_dataset
from ehrql import case, codelist_from_csv, create_dataset, days, when
from ehrql.tables.core import medications, patients
from ehrql.tables.tpp import (
    addresses,
    apcs,
    clinical_events,
    practice_registrations,
)

index_date = "2023-10-01"

dataset = create_dataset()

dataset.configure_dummy_data(population_size=100)

# codelists

ethnicity_codelist = codelist_from_csv(
    "codelists/opensafely-ethnicity.csv",
    column="Code",
    category_column="Grouping_6",
)

asthma_inhaler_codelist = codelist_from_csv(
    "codelists/opensafely-asthma-inhaler-salbutamol-medication.csv",
    column="code",
    category_column="term",
)

# population variables

was_female_or_male = patients.sex.is_in(["female", "male"])

was_adult = (patients.age_on(index_date) >= 18) & (patients.age_on(index_date) <= 110)

was_alive = (
    patients.date_of_death.is_after(index_date) | patients.date_of_death.is_null()
)

was_registered = practice_registrations.for_patient_on(index_date).exists_for_patient()

dataset.define_population(was_female_or_male & was_adult & was_alive & was_registered)

# demographic variables

dataset.age = patients.age_on(index_date)

dataset.sex = patients.sex

dataset.ethnicity = (
    clinical_events.where(clinical_events.ctv3_code.is_in(ethnicity_codelist))
    .sort_by(clinical_events.date)
    .last_for_patient()
    .ctv3_code.to_category(ethnicity_codelist)
)

imd_rounded = addresses.for_patient_on(index_date).imd_rounded
max_imd = 32844

dataset.imd_quintile = case(
    when(imd_rounded < int(max_imd * 1 / 5)).then(1),
    when(imd_rounded < int(max_imd * 2 / 5)).then(2),
    when(imd_rounded < int(max_imd * 3 / 5)).then(3),
    when(imd_rounded < int(max_imd * 4 / 5)).then(4),
    when(imd_rounded <= max_imd).then(5),
)

# exposure variable

dataset.num_asthma_inhaler_medications = (
    medications.where(medications.dmd_code.is_in(asthma_inhaler_codelist))
    .where(medications.date.is_on_or_between(index_date - days(30), index_date))
    .count_for_patient()
)

# outcome variable

dataset.date_patient_was_first_admitted = (
    apcs.where(apcs.admission_date.is_after(index_date))
    .sort_by(apcs.admission_date)
    .first_for_patient()
    .admission_date
)

# No longer needed
# from ehrql import create_dataset
# from ehrql.tables.core import patients, medications
# dataset = create_dataset()
# dataset.define_population(patients.date_of_birth.is_on_or_before("1999-12-31"))
# asthma_codes = ["39113311000001107", "39113611000001102"]
# latest_asthma_med = (
#     medications.where(medications.dmd_code.is_in(asthma_codes))
#     .sort_by(medications.date)
#     .last_for_patient()
# )
# dataset.asthma_med_date = latest_asthma_med.date
# dataset.asthma_med_code = latest_asthma_med.dmd_code

