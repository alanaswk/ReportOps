# ReportOps Reporting Handbook

## Data Requirements

ReportOps expects operational reporting data at the location-month level.

Required fields are:

* `location_id`: unique identifier for the location.
* `location_name`: readable location name.
* `region`: region associated with the location.
* `month`: reporting month.
* `revenue`: actual revenue for the reporting period.
* `budget_revenue`: budgeted revenue for the reporting period.
* `labor_expense`: actual labor expense.
* `other_expense`: other operating expense.
* `total_expense`: total operating expense.
* `volume`: operational activity volume.

Each location should have no more than one record for each reporting month.

## Revenue Variance to Budget

Revenue variance measures the difference between actual revenue and budgeted revenue.

Revenue variance amount is calculated as:

actual revenue - budget revenue

Revenue variance percentage is calculated as:

(actual revenue - budget revenue) / budget revenue

A positive variance means actual revenue exceeded budget. A negative variance means actual revenue was below budget.

When budget revenue is zero, the percentage variance should not be calculated because division by zero would make the result undefined.

## Month-over-Month Revenue Change

Month-over-month revenue change compares revenue for one reporting month with revenue from the immediately preceding month.

The change amount is calculated as:

current month revenue - prior month revenue

The percentage change is calculated as:

(current month revenue - prior month revenue) / prior month revenue

A positive result represents revenue growth. A negative result represents a decline.

The first available month does not have a prior month and therefore does not have a month-over-month comparison.

## Operating Margin

Operating margin measures how much revenue remains after operating expenses.

Operating margin is calculated as:

(revenue - total operating expense) / revenue

Total operating expense consists of labor expense plus other expense.

A higher operating margin indicates that a larger proportion of revenue remains after operating expenses.

Operating margin should not be calculated when revenue is zero.

## Labor Expense Percentage

Labor expense percentage measures labor expense relative to revenue.

It is calculated as:

labor expense / revenue

The metric shows what portion of revenue is consumed by labor costs.

Labor expense percentage should not be calculated when revenue is zero.

## Validation Rules

### Missing Required Columns

A file is invalid when one or more fields required by the reporting workflow are absent.

Missing required columns are treated as high-severity issues because ReportOps may be unable to validate the data or calculate required metrics reliably.

### Duplicate Records

A duplicate exists when more than one record contains the same location and reporting month.

Duplicate location-month records may cause revenue, expenses, volume, and other metrics to be counted more than once.

Duplicate records should be reviewed before report results are used.

### Missing Values

Required identifiers and numeric reporting fields should not contain missing values.

Missing values can make calculations incomplete or cause records to be excluded from analysis.

The missing field should be reviewed against the source data before reporting continues.

### Impossible Values

ReportOps flags values that violate basic reporting constraints.

Examples include negative operational volume and dates that cannot be interpreted as valid reporting periods.

These values should be checked against the original source because they may indicate data-entry or formatting errors.

### Expense Reconciliation

Total expense should reconcile to its components.

The expected relationship is:

labor expense + other expense = total expense

A record is flagged when the supplied total expense differs from the sum of its components beyond the allowed reconciliation tolerance.

A reconciliation error can cause operating margin and other expense-based metrics to be incorrect.

## Validation Severity Guidance

High-severity issues prevent reliable reporting or calculation and should normally be resolved before results are used.

Medium-severity issues indicate that some results may still be calculated but should be interpreted carefully.

Validation messages should explain the problem, why it matters, and the recommended corrective action.

ReportOps does not automatically change or repair source data.

## Variance Review Guidance

Revenue variance should be reviewed in both dollar and percentage terms.

Large dollar variances may be important even when the percentage change is relatively small.

Large percentage variances may also require review when they occur at smaller locations.

ReportOps does not assign an arbitrary good or bad threshold unless a threshold has been explicitly supplied by the reporting rules.

Users should consider both the magnitude and direction of a variance when investigating performance.

## Chart Selection Guidance

Use the actual-versus-budget chart when comparing actual revenue with budgeted revenue across locations or reporting groups.

Use the monthly revenue trend chart when evaluating how revenue changes over time.

Use the largest-variances chart when identifying the locations or reporting groups with the greatest differences between actual and budgeted revenue.

Charts are intended to visualize already validated and calculated results. They should not replace validation or deterministic metric calculations.
