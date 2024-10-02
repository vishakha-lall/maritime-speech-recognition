import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, html, dcc
from dash.dependencies import Input, Output
import pandas as pd
import numpy as np

from database_session_utils import get_engine
from demanding_event_orm_crud import get_all_demanding_events_by_client_id, get_demanding_event_by_id
from demanding_event_session_mapping_orm_crud import get_demanding_event_session_mapping_by_session_id_demanding_event_id
from session_orm_crud import get_session_by_subject_id_exercise_id
from subject_orm_crud import get_all_subjects_by_client_id, get_subject_by_id


def fetch_subjects(client_id):
    subjects = get_all_subjects_by_client_id(client_id)
    df = pd.DataFrame.from_records([s.to_dict() for s in subjects])
    return df


def fetch_demanding_events(client_id):
    demanding_events = get_all_demanding_events_by_client_id(client_id)
    df = pd.DataFrame.from_records([s.to_dict() for s in demanding_events])
    return df


def create_subject_wise_entity_plot(subject_id, exercise_id, demanding_event_id):
    subject = get_subject_by_id(subject_id)
    demanding_event = get_demanding_event_by_id(demanding_event_id)
    engine = get_engine()
    df = pd.read_sql(
        f'SELECT e.communication_level, e.addressed_entity, s.exercise_id FROM extracted_entity e JOIN session s ON e.session_id = s.id WHERE s.subject_id = {subject_id} and e.demanding_event_id = {demanding_event_id} and s.exercise_id = {exercise_id};', con=engine)
    grouped_data = df.groupby(
        ['communication_level', 'addressed_entity']).size().reset_index(name='counts')
    fig = px.sunburst(
        grouped_data,
        path=['communication_level', 'addressed_entity'],
        values='counts',
        title=f"Subject {subject.alias} Demanding Event {demanding_event.type} Exercise {exercise_id} Extracted Entities"
    )
    fig.update_traces(insidetextorientation='radial')
    fig.update_layout(
        height=600,
        width=800,
    )
    return fig


def create_all_subjects_entity_plot(client_id, selected_subject_id, exercise_id, demanding_event_id):
    demanding_event = get_demanding_event_by_id(demanding_event_id)
    selected_subject = get_subject_by_id(selected_subject_id)
    engine = get_engine()
    df = pd.read_sql(
        f'SELECT e.communication_level, e.addressed_entity, s.exercise_id, sub.alias as subject FROM extracted_entity e JOIN session s ON e.session_id = s.id JOIN subject sub ON sub.id = s.subject_id WHERE e.demanding_event_id = {demanding_event_id} and s.client_id = {client_id} and s.exercise_id = {exercise_id};', con=engine)
    grouped_data = df.groupby(['subject', 'communication_level',
                              'addressed_entity']).size().reset_index(name='counts')
    total_counts_by_subject = grouped_data.groupby(
        ['subject'])['counts'].transform('sum')
    grouped_data['percentage'] = (
        grouped_data['counts'] / total_counts_by_subject) * 100
    fig = go.Figure()
    subjects = grouped_data['subject'].unique()
    for subject in subjects:
        df_subject = grouped_data[grouped_data['subject'] == subject]
        if subject == selected_subject.alias:
            fig.add_trace(go.Bar(
                x=df_subject['communication_level'] +
                ' - ' + df_subject['addressed_entity'],
                y=df_subject['percentage'],
                name=f'{subject} (Selected)',
                marker=dict(
                    color='rgba(0,0,255,0.7)',
                    pattern_shape="/"
                )
            ))
        else:
            fig.add_trace(go.Bar(
                x=df_subject['communication_level'] +
                ' - ' + df_subject['addressed_entity'],
                y=df_subject['percentage'],
                name=f'{subject}'
            ))
    fig.update_layout(
        title=f'Communication Entity Comparison for Exercise {exercise_id} Demanding Event {demanding_event.type}',
        barmode='group',
        xaxis_title='Communication Level - Addressed Entity',
        yaxis_title='Percentage of Communication',
        yaxis=dict(range=[0, 100]),
        height=600
    )
    return fig


def create_subject_wise_checklist_adherence_table(subject_id, exercise_id, demanding_event_id):
    subject = get_subject_by_id(subject_id)
    demanding_event = get_demanding_event_by_id(demanding_event_id)
    session = get_session_by_subject_id_exercise_id(subject_id, exercise_id)
    engine = get_engine()
    completed_df = pd.read_sql(
        f'SELECT c.description as checklist, a.is_completed, a.completion_time from checklist_item c JOIN checklist_item_adherence a ON c.id = a.checklist_item_id WHERE a.session_id = {session.id} AND a.demanding_event_id = {demanding_event_id};', con=engine)
    all_df = pd.read_sql(
        f'SELECT description as checklist, importance from checklist_item WHERE demanding_event_id = {demanding_event_id};', con=engine)
    all_df['is_completed'] = all_df['checklist'].apply(
        lambda x: 'yes' if all(completed_df.loc[completed_df['checklist'] == x, 'is_completed'] == 1) else 'no')
    result_df = all_df[['checklist', 'importance', 'is_completed']].sort_values(
        by='importance', ascending=False)
    result_df = all_df[['checklist', 'is_completed']]
    fig = go.Figure(data=[go.Table(
        header=dict(
            values=list(result_df.columns),
            fill_color='paleturquoise',
            align='left'
        ),
        cells=dict(
            values=[result_df[col] for col in result_df.columns],
            fill_color='lavender',
            align='left'
        )
    )])
    fig.update_layout(
        title=f"Subject {subject.alias} Demanding Event {demanding_event.type} Exercise {exercise_id} Checklist Adherence",
        margin=dict(l=50, r=50, t=50, b=50)
    )
    return fig


def create_all_subjects_response_correctness_plot(client_id, exercise_id, demanding_event_id, selected_subject_id):
    subjects = get_all_subjects_by_client_id(client_id)
    demanding_event = get_demanding_event_by_id(demanding_event_id)
    selected_subject = get_subject_by_id(selected_subject_id)
    engine = get_engine()
    response_correctness = {}
    for subject in subjects:
        session = get_session_by_subject_id_exercise_id(subject.id, exercise_id)
        if session:
            if get_demanding_event_session_mapping_by_session_id_demanding_event_id(session.id, demanding_event.id):
                completed_df = pd.read_sql(
                f'SELECT c.description as checklist, a.is_completed, a.completion_time from checklist_item c JOIN checklist_item_adherence a ON c.id = a.checklist_item_id WHERE a.session_id = {session.id} AND a.demanding_event_id = {demanding_event_id};', con=engine)
                all_df = pd.read_sql(
                    f'SELECT description as checklist, importance from checklist_item WHERE demanding_event_id = {demanding_event_id};', con=engine)
                all_df['is_completed'] = all_df['checklist'].apply(lambda x: 'yes' if all(completed_df.loc[completed_df['checklist'] == x, 'is_completed'] == 1) else 'no')
                response_correctness_for_subject = all_df[all_df['is_completed'] == 'yes']['importance'].sum(
                )/all_df['importance'].sum()*100
                response_correctness[subject.alias] = response_correctness_for_subject
    fig = go.Figure()
    aliases = list(response_correctness.keys())
    correctness_values = list(response_correctness.values())
    fig.add_trace(go.Bar(
        x=aliases,
        y=correctness_values,
        name='All Subjects',
        marker=dict(
            color=['red' if subject ==
                   selected_subject.alias else 'blue' for subject in aliases],
            pattern_shape=[
                '/' if subject == selected_subject.alias else '' for subject in aliases]
        )
    ))
    fig.update_layout(
        title=f'Response Correctness Comparison for Exercise {exercise_id} Demanding Event {demanding_event.type}',
        xaxis_title='Subject',
        yaxis_title='Response Correctness Percentage',
        yaxis=dict(range=[0, 100]),
        showlegend=False
    )
    return fig


def create_all_subjects_response_time_plot(exercise_id, demanding_event_id, selected_subject_id):
    demanding_event = get_demanding_event_by_id(demanding_event_id)
    selected_subject = get_subject_by_id(selected_subject_id)
    engine = get_engine()
    completed_df = pd.read_sql(
        f'SELECT sub.alias as subject, c.description as checklist, a.is_completed, a.completion_time, map.time_start from checklist_item c JOIN checklist_item_adherence a ON c.id = a.checklist_item_id JOIN session s ON a.session_id = s.id JOIN subject sub ON s.subject_id = sub.id JOIN demanding_event_session_mapping map ON map.session_id = s.id WHERE a.demanding_event_id = {demanding_event_id} AND s.exercise_id = {exercise_id} AND map.demanding_event_id = {demanding_event_id};', con=engine)
    completed_df['completion_time'] = np.maximum(
        completed_df['completion_time'] - completed_df['time_start'], 0)
    grouped_data = completed_df.groupby(['subject'], as_index=False).agg(
        response_time=('completion_time', 'min'))
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=grouped_data['subject'],
        y=grouped_data['response_time'],
        name='All Subjects',
        marker=dict(
            color=['red' if subject ==
                   selected_subject.alias else 'blue' for subject in grouped_data['subject']],
            pattern_shape=[
                '/' if subject == selected_subject.alias else '' for subject in grouped_data['subject']]
        )
    ))
    fig.update_layout(
        title=f'Response Time Comparison for Exercise {exercise_id} Demanding Event {demanding_event.type}',
        xaxis_title='Subject',
        yaxis_title='Response Time (sec)',
        showlegend=False
    )
    return fig


app = Dash()

client_id = 1
subject_options = [{'label': row['subject'], 'value': int(
    row['id'])} for _, row in fetch_subjects(client_id).iterrows()]
demanding_event_options = [{'label': row['demanding_event'], 'value': row['id']}
                           for _, row in fetch_demanding_events(client_id).iterrows()]

app.layout = html.Div([
    html.H2("Communication Analysis"),
    html.Div([
        html.H4("Subject"),
        dcc.Dropdown(
            id='subject-dropdown',
            options=subject_options,
            style={'display': 'inline-block', 'width': '30%'}
        ),
        html.H4("Demanding Event"),
        dcc.Dropdown(
            id='demanding-event-dropdown',
            options=demanding_event_options,
            style={'display': 'inline-block', 'width': '30%'}
        )
    ]),
    html.H3("Extracted Communication Entities"),
    html.Div([
        dcc.Graph(id='communication-ind-exer-1',
                  style={'display': 'inline-block', 'width': '48%'}),
        dcc.Graph(id='communication-ind-exer-2',
                  style={'display': 'inline-block', 'width': '48%'}),
    ]),
    html.Div([
        dcc.Graph(id='communication-comp-exer-1',
                  style={'display': 'inline-block', 'width': '48%'}),
        dcc.Graph(id='communication-comp-exer-2',
                  style={'display': 'inline-block', 'width': '48%'}),
    ]),
    html.H3("Adherence to Communication Checklist"),
    html.Div([
        dcc.Graph(id='checklist-exer-1',
                  style={'display': 'inline-block', 'width': '48%'}),
        dcc.Graph(id='checklist-exer-2',
                  style={'display': 'inline-block', 'width': '48%'}),
    ]),
    html.Div([
        dcc.Graph(id='correctness-com-exer-1',
                  style={'display': 'inline-block', 'width': '48%'}),
        dcc.Graph(id='correctness-com-exer-2',
                  style={'display': 'inline-block', 'width': '48%'}),
    ]),
    html.Div([
        dcc.Graph(id='response-time-hist-exer-1',
                  style={'display': 'inline-block', 'width': '48%'}),
        dcc.Graph(id='response-time-hist-exer-2',
                  style={'display': 'inline-block', 'width': '48%'}),
    ]),
])


@app.callback(
    [Output('communication-ind-exer-1', 'figure'), Output('communication-ind-exer-2', 'figure'), Output('communication-comp-exer-1', 'figure'),
     Output('communication-comp-exer-2', 'figure'), Output('checklist-exer-1', 'figure'), Output('checklist-exer-2', 'figure'),  Output('correctness-com-exer-1', 'figure'), Output('correctness-com-exer-2', 'figure'), Output('response-time-hist-exer-1', 'figure'), Output('response-time-hist-exer-2', 'figure')],
    [Input('subject-dropdown', 'value'),
     Input('demanding-event-dropdown', 'value')]
)
def update_subject(selected_subject, selected_demanding_event):
    fig_ex1 = create_subject_wise_entity_plot(
        selected_subject, 1, selected_demanding_event)
    fig_ex2 = create_subject_wise_entity_plot(
        selected_subject, 2, selected_demanding_event)
    fig_bar_ex1 = create_all_subjects_entity_plot(
        client_id, selected_subject, 1, selected_demanding_event)
    fig_bar_ex2 = create_all_subjects_entity_plot(
        client_id, selected_subject, 2, selected_demanding_event)
    fig_table_ex1 = create_subject_wise_checklist_adherence_table(
        selected_subject, 1, selected_demanding_event)
    fig_table_ex2 = create_subject_wise_checklist_adherence_table(
        selected_subject, 2, selected_demanding_event)
    fig_response_comp_ex1 = create_all_subjects_response_correctness_plot(
        client_id, 1, selected_demanding_event, selected_subject)
    fig_response_comp_ex2 = create_all_subjects_response_correctness_plot(
        client_id, 2, selected_demanding_event, selected_subject)
    fig_hist_resp_time_ex1 = create_all_subjects_response_time_plot(
        1, selected_demanding_event, selected_subject)
    fig_hist_resp_time_ex2 = create_all_subjects_response_time_plot(
        2, selected_demanding_event, selected_subject)
    return fig_ex1, fig_ex2, fig_bar_ex1, fig_bar_ex2, fig_table_ex1, fig_table_ex2, fig_response_comp_ex1, fig_response_comp_ex2, fig_hist_resp_time_ex1, fig_hist_resp_time_ex2


if __name__ == '__main__':
    app.run(debug=True)
