import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from dash import Dash, html, dcc
from database_session_utils import get_engine
from subject_orm_crud import get_all_subjects_by_client_id, get_subject_by_id
from demanding_event_orm_crud import get_demanding_event_by_id
from session_orm_crud import get_session_by_id, get_sessions_by_subject_id
from demanding_event_session_mapping_orm_crud import get_demanding_event_session_mapping_by_session_id, get_demanding_event_session_mapping_by_session_id_demanding_event_id

from scipy.stats import gaussian_kde
from dash.dependencies import Input, Output


def fetch_subjects(client_id):
    subjects = get_all_subjects_by_client_id(client_id)
    df = pd.DataFrame.from_records([s.to_dict() for s in subjects])
    return df


def fetch_demanding_events(subject_id):
    sessions = get_sessions_by_subject_id(subject_id)
    demanding_event_ids = []
    for session in sessions:
        demanding_event_ids.extend(
            [demanding_event_session_mapping.demanding_event_id for demanding_event_session_mapping in get_demanding_event_session_mapping_by_session_id(session.id)])
    demanding_events = [get_demanding_event_by_id(
        id) for id in demanding_event_ids]
    df = pd.DataFrame.from_records([s.to_dict() for s in demanding_events])
    return df


def create_subject_wise_entity_plot(subject_id, demanding_event_id):
    sessions = get_sessions_by_subject_id(subject_id)
    demanding_event_session_mappings = [get_demanding_event_session_mapping_by_session_id_demanding_event_id(
        session.id, demanding_event_id) for session in sessions]
    session_id = None
    for mapping in demanding_event_session_mappings:
        if mapping is None:
            continue
        else:
            session_id = mapping.session_id
    subject = get_subject_by_id(subject_id)
    demanding_event = get_demanding_event_by_id(demanding_event_id)
    engine = get_engine()
    df = pd.read_sql(
        f'''
        SELECT 
            communication_level, addressed_entity
        FROM
            extracted_entity
        WHERE
            demanding_event_id = {demanding_event_id}
                AND session_id = {session_id};''', con=engine)
    grouped_data = df.groupby(
        ['communication_level', 'addressed_entity']).size().reset_index(name='counts')
    fig = px.sunburst(
        grouped_data,
        path=['communication_level', 'addressed_entity'],
        values='counts',
        title=f"Subject {subject.alias} Demanding Event {demanding_event.type} Extracted Entities"
    )
    fig.update_traces(insidetextorientation='radial')
    fig.update_layout(
        height=600,
        width=800,
    )
    return fig


def create_all_subjects_entity_plot(client_id, selected_subject_id, demanding_event_id):
    selected_subject = get_subject_by_id(selected_subject_id)
    demanding_event = get_demanding_event_by_id(demanding_event_id)
    engine = get_engine()
    df = pd.read_sql(
        f'''
        SELECT 
            e.communication_level,
            e.addressed_entity,
            s.exercise_id,
            sub.alias AS subject
        FROM
            extracted_entity e
                JOIN
            session s ON e.session_id = s.id
                JOIN
            subject sub ON sub.id = s.subject_id
        WHERE
            e.demanding_event_id = {demanding_event_id}
                AND s.client_id = {client_id};''', con=engine)
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
        title=f'Communication Entity Comparison for Demanding Event {demanding_event.type}',
        barmode='group',
        xaxis_title='Communication Level - Addressed Entity',
        yaxis_title='Percentage of Communication',
        yaxis=dict(range=[0, 100]),
        height=600
    )
    return fig


def create_subject_wise_checklist_adherence_table(subject_id, demanding_event_id):
    subject = get_subject_by_id(subject_id)
    demanding_event = get_demanding_event_by_id(demanding_event_id)
    sessions = get_sessions_by_subject_id(subject_id)
    demanding_event_session_mappings = [get_demanding_event_session_mapping_by_session_id_demanding_event_id(
        session.id, demanding_event_id) for session in sessions]
    session_id = None
    for mapping in demanding_event_session_mappings:
        if mapping is None:
            continue
        else:
            session_id = mapping.session_id
    session = get_session_by_id(session_id)
    engine = get_engine()
    completed_df = pd.read_sql(
        f'''SELECT 
            c.description AS checklist,
            a.is_completed,
            a.completion_time
        FROM
            checklist_item c
                JOIN
            checklist_item_adherence a ON c.id = a.checklist_item_id
        WHERE
            a.session_id = {session.id}
            AND a.demanding_event_id = {demanding_event_id};''', con=engine)
    all_df = pd.read_sql(
        f'''SELECT 
            description as checklist, 
            importance from checklist_item 
        WHERE demanding_event_id = {demanding_event_id};''', con=engine)
    all_df['is_completed'] = all_df['checklist'].apply(
        lambda x: 'yes' if any(completed_df.loc[completed_df['checklist'] == x, 'is_completed'] == 1) else 'no')
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
        title=f"Subject {subject.alias} Demanding Event {demanding_event.type} Checklist Adherence",
        margin=dict(l=50, r=50, t=50, b=50)
    )
    return fig


def create_all_subjects_response_correctness_plot(client_id, demanding_event_id, selected_subject_id):
    subjects = get_all_subjects_by_client_id(client_id)
    demanding_event = get_demanding_event_by_id(demanding_event_id)
    selected_subject = get_subject_by_id(selected_subject_id)
    engine = get_engine()
    response_correctness = {}
    for subject in subjects:
        sessions = get_sessions_by_subject_id(subject.id)
        demanding_event_session_mappings = [get_demanding_event_session_mapping_by_session_id_demanding_event_id(
            session.id, demanding_event_id) for session in sessions]
        session_id = None
        for mapping in demanding_event_session_mappings:
            if mapping is None:
                continue
            else:
                session_id = mapping.session_id
        session = get_session_by_id(session_id)
        if session:
            engine = get_engine()
            completed_df = pd.read_sql(
                f'''SELECT 
                    c.description AS checklist,
                    a.is_completed,
                    a.completion_time
                FROM
                    checklist_item c
                        JOIN
                    checklist_item_adherence a ON c.id = a.checklist_item_id
                WHERE
                    a.session_id = {session.id}
                        AND a.demanding_event_id = {demanding_event_id};''', con=engine)
            all_df = pd.read_sql(
                f'SELECT description as checklist, importance from checklist_item WHERE demanding_event_id = {demanding_event_id};', con=engine)
            all_df['is_completed'] = all_df['checklist'].apply(
                lambda x: 'yes' if any(completed_df.loc[completed_df['checklist'] == x, 'is_completed'] == 1) else 'no')
            response_correctness_for_subject = all_df[all_df['is_completed'] == 'yes']['importance'].sum(
            )/all_df['importance'].sum()*100
            response_correctness[subject.alias] = response_correctness_for_subject
    fig = go.Figure()
    aliases = list(response_correctness.keys())
    correctness_values = list(response_correctness.values())
    for alias, correctness in zip(aliases, correctness_values):
        fig.add_trace(go.Bar(
            x=[alias],
            y=[correctness],
            name=alias,
            legendgroup=alias,
            marker=dict(
                color=('red' if alias == selected_subject.alias else 'blue'),
                pattern_shape=('/' if alias == selected_subject.alias else ''))
        ))
    median = np.median(correctness_values)
    percentile_25 = np.percentile(correctness_values, 25)
    percentile_75 = np.percentile(correctness_values, 75)
    fig.add_shape(
        type="line",
        x0=-0.5, x1=len(aliases)-0.5,
        y0=median, y1=median,
        line=dict(color="green", width=2, dash="dash"),
        name="Median"
    )
    fig.add_shape(
        type="line",
        x0=-0.5, x1=len(aliases)-0.5,
        y0=percentile_25, y1=percentile_25,
        line=dict(color="blue", width=2, dash="dot"),
        name="25th Percentile"
    )
    fig.add_shape(
        type="line",
        x0=-0.5, x1=len(aliases)-0.5,
        y0=percentile_75, y1=percentile_75,
        line=dict(color="purple", width=2, dash="dot"),
        name="75th Percentile"
    )
    fig.add_annotation(
        x=len(aliases)+2.5, y=median,
        text=f"Median: {median:.2f}%",
        showarrow=False,
        yshift=10,
        font=dict(color="green")
    )
    fig.add_annotation(
        x=len(aliases)+2.5, y=percentile_25,
        text=f"25th Percentile: {percentile_25:.2f}%",
        showarrow=False,
        yshift=20,
        font=dict(color="blue")
    )
    fig.add_annotation(
        x=len(aliases)+2.5, y=percentile_75,
        text=f"75th Percentile: {percentile_75:.2f}%",
        showarrow=False,
        yshift=-10,
        font=dict(color="purple")
    )
    fig.update_layout(
        title=f'Response Correctness Comparison for Demanding Event {demanding_event.type}',
        xaxis_title='Subject',
        yaxis_title='Response Correctness Percentage',
        yaxis=dict(range=[0, 100]),
        showlegend=True
    )
    return fig


def create_all_subjects_response_time_plot(demanding_event_id, selected_subject_id):
    demanding_event = get_demanding_event_by_id(demanding_event_id)
    selected_subject = get_subject_by_id(selected_subject_id)
    engine = get_engine()
    completed_df = pd.read_sql(
        f'''SELECT 
                sub.alias AS subject,
                c.description AS checklist,
                a.is_completed,
                a.completion_time,
                map.time_start
            FROM
                checklist_item c
                    JOIN
                checklist_item_adherence a ON c.id = a.checklist_item_id
                    JOIN
                session s ON a.session_id = s.id
                    JOIN
                subject sub ON s.subject_id = sub.id
                    JOIN
                demanding_event_session_mapping map ON map.session_id = s.id
            WHERE
                a.demanding_event_id = {demanding_event_id}
                    AND map.demanding_event_id = {demanding_event_id};''', con=engine)
    completed_df['completion_time'] = np.maximum(
        completed_df['completion_time'] - completed_df['time_start'], 0)
    grouped_data = completed_df.groupby(['subject'], as_index=False).agg(
        response_time=('completion_time', 'min'))
    response_times = grouped_data['response_time']
    kde = gaussian_kde(response_times)
    x_vals = np.linspace(min(response_times), max(response_times), 500)
    y_vals = kde(x_vals)
    selected_response_time = grouped_data[grouped_data['subject']
                                          == selected_subject.alias]['response_time'].values[0]
    median = np.median(response_times)
    percentile_25 = np.percentile(response_times, 25)
    percentile_75 = np.percentile(response_times, 75)
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=x_vals,
        y=y_vals,
        mode='lines',
        name="Response Times for all Subjects",
        line=dict(color='blue')
    ))
    fig.add_shape(
        type="line",
        x0=selected_response_time,
        y0=0,
        x1=selected_response_time,
        y1=max(y_vals),
        line=dict(color="red", width=3, dash="dash"),
        name=f"Selected Subject: {selected_subject.alias}"
    )
    fig.add_shape(
        type="line",
        x0=median,
        y0=0,
        x1=median,
        y1=max(y_vals),
        line=dict(color="green", width=3, dash="dash"),
        name=f"Median: {median}"
    )
    fig.add_shape(
        type="line",
        x0=percentile_25,
        y0=0,
        x1=percentile_25,
        y1=max(y_vals),
        line=dict(color="blue", width=3, dash="dash"),
        name=f"25th Percentile: {percentile_25}"
    )
    fig.add_shape(
        type="line",
        x0=percentile_75,
        y0=0,
        x1=percentile_75,
        y1=max(y_vals),
        line=dict(color="purple", width=3, dash="dash"),
        name=f"75th Percentile: {percentile_75}"
    )
    fig.add_annotation(
        x=selected_response_time, y=min(y_vals),
        text=f"{selected_subject.alias}: {selected_response_time:.2f}",
        showarrow=False,
        textangle=90,
        yanchor='bottom',
        xshift=10,
        font=dict(color="purple")
    )
    fig.add_annotation(
        x=median, y=min(y_vals),
        text=f"Median: {median:.2f}",
        showarrow=False,
        textangle=90,
        yanchor='bottom',
        xshift=10,
        font=dict(color="green")
    )
    fig.add_annotation(
        x=percentile_25, y=min(y_vals),
        text=f"25th Percentile: {percentile_25:.2f}",
        showarrow=False,
        textangle=90,
        yanchor='bottom',
        xshift=10,
        font=dict(color="blue")
    )
    fig.add_annotation(
        x=percentile_75, y=min(y_vals),
        text=f"75th Percentile: {percentile_75:.2f}",
        showarrow=False,
        textangle=90,
        yanchor='bottom',
        xshift=10,
        font=dict(color="purple")
    )
    fig.update_layout(
        title=f'Response Time Histogram for Demanding Event {demanding_event.type}',
        xaxis_title='Response Time (seconds)',
        yaxis_title='Distribution of Subjects',
        yaxis=dict(showticklabels=False),
        showlegend=False
    )
    return fig


app = Dash()

client_id = 2
subject_options = [{'label': row['subject'], 'value': int(
    row['id'])} for _, row in fetch_subjects(client_id).iterrows()]


@app.callback(
    Output('demanding-event-dropdown', 'options'),
    [Input('subject-dropdown', 'value')]
)
def update_demanding_event_options(selected_subject):
    if selected_subject is not None:
        demanding_event_options = [{'label': row['demanding_event'], 'value': row['id']}
                                   for _, row in fetch_demanding_events(selected_subject).iterrows()]
        return demanding_event_options
    return []


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
            options=[],
            style={'display': 'inline-block', 'width': '30%'}
        )
    ]),
    html.H3("Extracted Communication Entities"),
    html.Div([
        dcc.Graph(id='communication-ind-exer-1',
                  style={'display': 'inline-block', 'width': '60%'})
    ]),
    html.Div([
        dcc.Graph(id='communication-comp-exer-1',
                  style={'display': 'inline-block', 'width': '60%'})
    ]),
    html.H3("Adherence to Communication Checklist"),
    html.Div([
        dcc.Graph(id='checklist-exer-1',
                  style={'display': 'inline-block', 'width': '60%'})
    ]),
    html.Div([
        dcc.Graph(id='correctness-com-exer-1',
                  style={'display': 'inline-block', 'width': '60%'}),
    ]),
    html.Div([
        dcc.Graph(id='response-time-hist-exer-1',
                  style={'display': 'inline-block', 'width': '60%'})
    ]),
])


@app.callback(
    [Output('communication-ind-exer-1', 'figure'), Output('communication-comp-exer-1', 'figure'),
     Output('checklist-exer-1', 'figure'), Output('correctness-com-exer-1', 'figure'), Output('response-time-hist-exer-1', 'figure')],
    [Input('subject-dropdown', 'value'),
     Input('demanding-event-dropdown', 'value')]
)
def update_subject(selected_subject, selected_demanding_event):
    fig_ex1 = create_subject_wise_entity_plot(
        selected_subject, selected_demanding_event)
    fig_bar_ex1 = create_all_subjects_entity_plot(
        client_id, selected_subject, selected_demanding_event)
    fig_table_ex1 = create_subject_wise_checklist_adherence_table(
        selected_subject, selected_demanding_event)
    fig_hist_resp_time_ex1 = create_all_subjects_response_time_plot(
        selected_demanding_event, selected_subject)
    fig_response_comp_ex1 = create_all_subjects_response_correctness_plot(
        client_id, selected_demanding_event, selected_subject)
    return fig_ex1, fig_bar_ex1, fig_table_ex1, fig_response_comp_ex1, fig_hist_resp_time_ex1


if __name__ == '__main__':
    app.run(debug=True)
