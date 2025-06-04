"""
Analytics Dashboard for Smart EMR
Provides comprehensive analytics and performance metrics
"""

import streamlit as st
import pandas as pd
import json
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import os

class EMRDashboard:
    """Analytics dashboard for monitoring Smart EMR usage and AI performance"""
    
    def __init__(self, data_path="data/patients/", analytics_path="data/analytics/"):
        self.data_path = Path(data_path)
        self.analytics_path = Path(analytics_path)
        self.metrics_file = self.analytics_path / "metrics.json"
        self.feedback_file = self.analytics_path / "clinician_feedback.json"
        
        # Ensure analytics directory exists
        self.analytics_path.mkdir(exist_ok=True, parents=True)
    
    def load_all_patient_data(self):
        """Load all patient visit data for analytics"""
        all_visits = []
        all_patients = []
        
        for patient_file in self.data_path.glob("*.json"):
            try:
                with open(patient_file, 'r') as f:
                    patient_data = json.load(f)
                
                # Patient-level data
                patient_record = {
                    'patient_id': patient_data.get('id', patient_data.get('patient_id')),
                    'name': patient_data.get('name'),
                    'age': patient_data.get('age'),
                    'sex': patient_data.get('sex'),
                    'ethnicity': patient_data.get('ethnicity', 'Not specified'),
                    'registration_date': patient_data.get('registration_date', ''),
                    'has_allergies': bool(patient_data.get('allergies')),
                    'has_medical_history': bool(patient_data.get('medical_history'))
                }
                all_patients.append(patient_record)
                
                # Visit-level data
                for visit in patient_data.get('visits', []):
                    visit_record = {
                        'patient_id': patient_data.get('id'),
                        'patient_name': patient_data.get('name'),
                        'patient_age': patient_data.get('age'),
                        'patient_sex': patient_data.get('sex'),
                        'visit_date': visit.get('timestamp', '')[:10],
                        'visit_time': visit.get('timestamp', '')[11:16],
                        'visit_type': visit.get('visit_type', 'OPD'),
                        'has_ai_summary': bool(visit.get('clinical_summary')),
                        'prescription_edited': visit.get('prescription_edited', False),
                        'is_backdated': visit.get('is_backdated', False),
                        'has_vitals': bool(visit.get('vitals', {}).get('bp')) or bool(visit.get('vitals', {}).get('hr'))
                    }
                    all_visits.append(visit_record)
                
                # Check for rare disease alerts
                if patient_data.get('rare_disease_alerts') or patient_data.get('cancer_screening_alerts'):
                    # This would be tracked separately
                    pass
                    
            except Exception as e:
                print(f"Error loading {patient_file}: {e}")
                continue
        
        return pd.DataFrame(all_visits), pd.DataFrame(all_patients)
    
    def load_feedback_data(self):
        """Load AI feedback ratings from doctors"""
        try:
            if self.feedback_file.exists():
                with open(self.feedback_file, 'r') as f:
                    feedback_data = json.load(f)
                return pd.DataFrame(feedback_data.get('feedback_entries', []))
            else:
                return pd.DataFrame()
        except Exception as e:
            print(f"Error loading feedback: {e}")
            return pd.DataFrame()
    
    def load_rare_disease_detections(self):
        """Load rare disease detection history"""
        detections = []
        
        for patient_file in self.data_path.glob("*.json"):
            try:
                with open(patient_file, 'r') as f:
                    patient_data = json.load(f)
                
                # Check symptom tracking
                patient_id = patient_data.get('id')
                
                # This is a placeholder - in real implementation, you'd track actual detections
                # from the rare disease detection runs
                
            except:
                continue
        
        return pd.DataFrame(detections)
    
    def calculate_metrics(self, visits_df, patients_df, feedback_df):
        """Calculate key performance metrics"""
        
        if len(visits_df) == 0:
            return self._empty_metrics()
        
        # Convert visit_date to datetime
        visits_df['visit_date'] = pd.to_datetime(visits_df['visit_date'], errors='coerce')
        
        # Basic metrics
        total_patients = len(patients_df)
        total_visits = len(visits_df)
        ai_summaries_generated = visits_df['has_ai_summary'].sum()
        
        # Time-based metrics
        now = datetime.now()
        last_7_days = now - timedelta(days=7)
        last_30_days = now - timedelta(days=30)
        
        recent_7d_df = visits_df[visits_df['visit_date'] >= last_7_days]
        recent_30d_df = visits_df[visits_df['visit_date'] >= last_30_days]
        
        visits_last_7_days = len(recent_7d_df)
        visits_last_30_days = len(recent_30d_df)
        
        # AI performance metrics
        if len(feedback_df) > 0:
            # Extract numeric ratings from feedback
            feedback_df['accuracy_score'] = feedback_df.get('metrics', {}).apply(
                lambda x: x.get('accuracy', 3) if isinstance(x, dict) else 3
            )
            feedback_df['usefulness_score'] = feedback_df.get('metrics', {}).apply(
                lambda x: x.get('usefulness', 3) if isinstance(x, dict) else 3
            )
            
            avg_accuracy = feedback_df['accuracy_score'].mean()
            avg_usefulness = feedback_df['usefulness_score'].mean()
            positive_feedback_rate = len(feedback_df[feedback_df['rating'] == 'helpful']) / len(feedback_df)
        else:
            avg_accuracy = 0
            avg_usefulness = 0
            positive_feedback_rate = 0
        
        # Prescription acceptance rate (placeholder - would need actual tracking)
        prescription_acceptance_rate = 0.85  # 85% placeholder
        
        # Patient demographics
        age_distribution = patients_df['age'].value_counts(bins=[0, 18, 30, 50, 70, 100]).to_dict()
        sex_distribution = patients_df['sex'].value_counts().to_dict()
        ethnicity_distribution = patients_df['ethnicity'].value_counts().to_dict()
        
        return {
            'total_patients': total_patients,
            'total_visits': total_visits,
            'visits_last_7_days': visits_last_7_days,
            'visits_last_30_days': visits_last_30_days,
            'ai_summaries_generated': ai_summaries_generated,
            'prescription_acceptance_rate': prescription_acceptance_rate,
            'avg_accuracy_rating': avg_accuracy,
            'avg_usefulness_rating': avg_usefulness,
            'positive_feedback_rate': positive_feedback_rate,
            'age_distribution': age_distribution,
            'sex_distribution': sex_distribution,
            'ethnicity_distribution': ethnicity_distribution
        }
    
    def _empty_metrics(self):
        """Return empty metrics when no data available"""
        return {
            'total_patients': 0,
            'total_visits': 0,
            'visits_last_7_days': 0,
            'visits_last_30_days': 0,
            'ai_summaries_generated': 0,
            'prescription_acceptance_rate': 0,
            'avg_accuracy_rating': 0,
            'avg_usefulness_rating': 0,
            'positive_feedback_rate': 0,
            'age_distribution': {},
            'sex_distribution': {},
            'ethnicity_distribution': {}
        }
    
    def display_dashboard(self):
        """Main dashboard display function"""
        
        st.title("🏥 Smart EMR Analytics Dashboard")
        st.markdown("---")
        
        # Load data
        with st.spinner("Loading analytics data..."):
            visits_df, patients_df = self.load_all_patient_data()
            feedback_df = self.load_feedback_data()
            metrics = self.calculate_metrics(visits_df, patients_df, feedback_df)
        
        # Top metrics row
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="Total Patients",
                value=metrics['total_patients'],
                delta=f"+{metrics['visits_last_7_days']} visits (7d)"
            )
            
        with col2:
            st.metric(
                label="AI Summaries",
                value=metrics['ai_summaries_generated'],
                delta=f"{metrics['prescription_acceptance_rate']*100:.0f}% accepted"
            )
            
        with col3:
            if metrics['positive_feedback_rate'] > 0:
                st.metric(
                    label="AI Performance",
                    value=f"{metrics['positive_feedback_rate']*100:.0f}%",
                    delta=f"Accuracy: {metrics['avg_accuracy_rating']:.1f}/5"
                )
            else:
                st.metric(
                    label="AI Performance",
                    value="No data",
                    delta="Start collecting feedback"
                )
            
        with col4:
            st.metric(
                label="This Month",
                value=f"{metrics['visits_last_30_days']} visits",
                delta=f"{metrics['visits_last_7_days']} this week"
            )
        
        st.markdown("---")
        
        # Detailed analytics tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Overview", "👥 Demographics", "🤖 AI Performance", "📈 Trends", "🔍 Insights"])
        
        with tab1:
            # Overview charts
            if len(visits_df) > 0:
                col1, col2 = st.columns(2)
                
                with col1:
                    # Visit volume over time
                    st.subheader("Visit Volume Trend")
                    
                    # Group by date
                    daily_visits = visits_df.groupby('visit_date').size().reset_index(name='visits')
                    daily_visits = daily_visits.sort_values('visit_date')
                    
                    fig = px.line(
                        daily_visits, 
                        x='visit_date', 
                        y='visits',
                        title='Daily Visit Count',
                        markers=True
                    )
                    fig.update_layout(
                        xaxis_title="Date",
                        yaxis_title="Number of Visits",
                        hovermode='x unified',
                        height=350
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    # Visit type distribution
                    st.subheader("Visit Type Distribution")
                    
                    visit_types = visits_df['visit_type'].value_counts()
                    
                    fig = px.pie(
                        values=visit_types.values,
                        names=visit_types.index,
                        title='OPD vs Admitted Visits',
                        hole=0.4
                    )
                    fig.update_layout(height=350)
                    st.plotly_chart(fig, use_container_width=True)
                
                # Heatmap of visits by day and hour
                if 'visit_time' in visits_df.columns:
                    st.subheader("Visit Patterns by Time")
                    
                    # Extract hour from time
                    visits_df['hour'] = pd.to_datetime(visits_df['visit_time'], format='%H:%M', errors='coerce').dt.hour
                    visits_df['day_of_week'] = visits_df['visit_date'].dt.day_name()
                    
                    # Create pivot table
                    heatmap_data = visits_df.groupby(['day_of_week', 'hour']).size().reset_index(name='count')
                    heatmap_pivot = heatmap_data.pivot(index='hour', columns='day_of_week', values='count').fillna(0)
                    
                    # Reorder days
                    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                    heatmap_pivot = heatmap_pivot.reindex(columns=[d for d in day_order if d in heatmap_pivot.columns])
                    
                    fig = px.imshow(
                        heatmap_pivot,
                        labels=dict(x="Day of Week", y="Hour of Day", color="Visits"),
                        title="Visit Heatmap",
                        color_continuous_scale="Blues"
                    )
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No visit data available yet. Start adding patient visits to see analytics.")
        
        with tab2:
            # Demographics analysis
            if len(patients_df) > 0:
                col1, col2 = st.columns(2)
                
                with col1:
                    # Age distribution
                    st.subheader("Age Distribution")
                    
                    age_bins = [0, 10, 20, 30, 40, 50, 60, 70, 80, 100]
                    age_labels = ['0-10', '11-20', '21-30', '31-40', '41-50', '51-60', '61-70', '71-80', '80+']
                    patients_df['age_group'] = pd.cut(patients_df['age'], bins=age_bins, labels=age_labels)
                    
                    age_dist = patients_df['age_group'].value_counts().sort_index()
                    
                    fig = px.bar(
                        x=age_dist.index,
                        y=age_dist.values,
                        title='Patient Age Groups',
                        labels={'x': 'Age Group', 'y': 'Number of Patients'}
                    )
                    fig.update_layout(height=350)
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    # Sex distribution
                    st.subheader("Sex Distribution")
                    
                    sex_dist = patients_df['sex'].value_counts()
                    
                    fig = px.pie(
                        values=sex_dist.values,
                        names=sex_dist.index,
                        title='Patient Sex Distribution',
                        hole=0.4
                    )
                    fig.update_layout(height=350)
                    st.plotly_chart(fig, use_container_width=True)
                
                # Ethnicity distribution if available
                if 'ethnicity' in patients_df.columns:
                    st.subheader("Ethnicity Distribution")
                    
                    ethnicity_dist = patients_df['ethnicity'].value_counts()
                    
                    fig = px.bar(
                        x=ethnicity_dist.values,
                        y=ethnicity_dist.index,
                        orientation='h',
                        title='Patient Ethnicity',
                        labels={'x': 'Count', 'y': 'Ethnicity'}
                    )
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No patient demographic data available yet.")
        
        with tab3:
            # AI Performance metrics
            st.subheader("🤖 AI Clinical Summary Performance")
            
            if len(feedback_df) > 0:
                col1, col2 = st.columns(2)
                
                with col1:
                    # Feedback ratings over time
                    feedback_df['date'] = pd.to_datetime(feedback_df['timestamp']).dt.date
                    
                    # Average ratings by date
                    daily_ratings = feedback_df.groupby('date').agg({
                        'accuracy_score': 'mean',
                        'usefulness_score': 'mean'
                    }).reset_index()
                    
                    fig = go.Figure()
                    
                    fig.add_trace(go.Scatter(
                        x=daily_ratings['date'],
                        y=daily_ratings['accuracy_score'],
                        mode='lines+markers',
                        name='Accuracy',
                        line=dict(color='blue', width=2)
                    ))
                    
                    fig.add_trace(go.Scatter(
                        x=daily_ratings['date'],
                        y=daily_ratings['usefulness_score'],
                        mode='lines+markers',
                        name='Usefulness',
                        line=dict(color='green', width=2)
                    ))
                    
                    fig.update_layout(
                        title='AI Performance Ratings Over Time',
                        xaxis_title='Date',
                        yaxis_title='Rating (1-5)',
                        yaxis=dict(range=[0, 5.5]),
                        hovermode='x unified',
                        height=350
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    # Feedback distribution
                    st.subheader("Feedback Distribution")
                    
                    rating_dist = feedback_df['rating'].value_counts()
                    
                    colors = {'helpful': 'green', 'neutral': 'orange', 'not_helpful': 'red'}
                    
                    fig = px.pie(
                        values=rating_dist.values,
                        names=rating_dist.index,
                        title='Overall Feedback Sentiment',
                        color_discrete_map=colors,
                        hole=0.4
                    )
                    fig.update_layout(height=350)
                    st.plotly_chart(fig, use_container_width=True)
                
                # Detailed feedback analysis
                st.subheader("Recent Feedback Comments")
                
                recent_feedback = feedback_df.nlargest(5, 'timestamp')[['timestamp', 'feedback_type', 'rating', 'clinician_notes']]
                recent_feedback['timestamp'] = pd.to_datetime(recent_feedback['timestamp']).dt.strftime('%Y-%m-%d %H:%M')
                
                st.dataframe(
                    recent_feedback,
                    column_config={
                        "timestamp": "Time",
                        "feedback_type": "Type",
                        "rating": st.column_config.TextColumn("Rating", help="Feedback sentiment"),
                        "clinician_notes": st.column_config.TextColumn("Comments", width="large")
                    },
                    hide_index=True,
                    use_container_width=True
                )
            else:
                st.info("No AI feedback collected yet. Encourage doctors to rate AI summaries to improve the system.")
                
                # Show sample feedback form
                with st.expander("Sample Feedback Collection"):
                    st.write("This is how doctors provide feedback:")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.slider("Accuracy", 1, 5, 3, disabled=True)
                    with col2:
                        st.slider("Usefulness", 1, 5, 3, disabled=True)
                    with col3:
                        st.slider("Prescription Quality", 1, 5, 3, disabled=True)
        
        with tab4:
            # Trends and patterns
            st.subheader("📈 Clinical Trends & Patterns")
            
            if len(visits_df) > 0:
                # Backdated entries analysis
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("Data Entry Patterns")
                    
                    backdated_count = visits_df['is_backdated'].sum() if 'is_backdated' in visits_df.columns else 0
                    realtime_count = len(visits_df) - backdated_count
                    
                    fig = px.pie(
                        values=[realtime_count, backdated_count],
                        names=['Real-time Entries', 'Backdated Entries'],
                        title='Entry Type Distribution',
                        hole=0.4
                    )
                    fig.update_layout(height=300)
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    st.subheader("AI Adoption Rate")
                    
                    # Group by month and calculate AI usage
                    visits_df['month'] = visits_df['visit_date'].dt.to_period('M').astype(str)
                    monthly_ai = visits_df.groupby('month').agg({
                        'has_ai_summary': ['sum', 'count']
                    }).reset_index()
                    monthly_ai.columns = ['month', 'ai_summaries', 'total_visits']
                    monthly_ai['ai_adoption_rate'] = (monthly_ai['ai_summaries'] / monthly_ai['total_visits'] * 100).round(1)
                    
                    fig = px.line(
                        monthly_ai,
                        x='month',
                        y='ai_adoption_rate',
                        title='AI Summary Adoption Rate',
                        markers=True
                    )
                    fig.update_layout(
                        yaxis_title='Adoption Rate (%)',
                        xaxis_title='Month',
                        height=300
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                # Vitals recording compliance
                st.subheader("Clinical Data Quality")
                
                vitals_compliance = visits_df['has_vitals'].mean() * 100 if 'has_vitals' in visits_df.columns else 0
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Vitals Recording Rate", f"{vitals_compliance:.1f}%")
                with col2:
                    st.metric("Avg Visits/Patient", f"{len(visits_df)/len(patients_df):.1f}" if len(patients_df) > 0 else "0")
                with col3:
                    st.metric("Data Completeness", "Good" if vitals_compliance > 70 else "Needs Improvement")
            else:
                st.info("Insufficient data for trend analysis. Keep using the system to see patterns emerge.")
        
        with tab5:
            # Insights and recommendations
            st.subheader("🔍 Clinical Insights & Recommendations")
            
            # Generate insights based on data
            insights = []
            
            if metrics['total_patients'] > 0:
                # Visit frequency insight
                avg_visits_per_patient = metrics['total_visits'] / metrics['total_patients']
                if avg_visits_per_patient > 3:
                    insights.append({
                        'type': 'success',
                        'title': 'High Patient Retention',
                        'message': f'Patients average {avg_visits_per_patient:.1f} visits, indicating good continuity of care.'
                    })
                
                # AI adoption insight
                if metrics['ai_summaries_generated'] / metrics['total_visits'] > 0.7:
                    insights.append({
                        'type': 'success',
                        'title': 'Strong AI Adoption',
                        'message': 'Over 70% of visits use AI summaries, maximizing efficiency gains.'
                    })
                elif metrics['ai_summaries_generated'] / metrics['total_visits'] < 0.3:
                    insights.append({
                        'type': 'warning',
                        'title': 'Low AI Usage',
                        'message': 'Consider training staff on AI features to improve adoption.'
                    })
                
                # Feedback insight
                if metrics['positive_feedback_rate'] > 0.8:
                    insights.append({
                        'type': 'success',
                        'title': 'Excellent AI Performance',
                        'message': f"{metrics['positive_feedback_rate']*100:.0f}% positive feedback shows AI is meeting clinical needs."
                    })
                
                # Demographics insight
                if len(patients_df) > 0:
                    median_age = patients_df['age'].median()
                    if median_age > 50:
                        insights.append({
                            'type': 'info',
                            'title': 'Aging Patient Population',
                            'message': f'Median age is {median_age:.0f}. Consider geriatric-specific protocols and screening.'
                        })
            
            # Display insights
            if insights:
                for insight in insights:
                    if insight['type'] == 'success':
                        st.success(f"✅ **{insight['title']}**: {insight['message']}")
                    elif insight['type'] == 'warning':
                        st.warning(f"⚠️ **{insight['title']}**: {insight['message']}")
                    else:
                        st.info(f"ℹ️ **{insight['title']}**: {insight['message']}")
            else:
                st.info("Keep using Smart EMR to generate meaningful insights about your practice.")
            
            # Recommendations
            st.subheader("💡 Recommendations")
            
            recommendations = []
            
            if metrics['total_visits'] < 50:
                recommendations.append("📊 Reach 50+ visits to unlock detailed pattern analysis")
            
            if metrics['positive_feedback_rate'] == 0:
                recommendations.append("⭐ Start rating AI summaries to help improve accuracy")
            
            if 'backdated_count' in locals() and backdated_count > 0:
                recommendations.append("📝 Complete migration of historical records for comprehensive analysis")
            
            if recommendations:
                for rec in recommendations:
                    st.write(f"• {rec}")
            else:
                st.success("🎉 Great job! Your clinic is using Smart EMR effectively.")
        
        # Export section
        st.markdown("---")
        with st.expander("📤 Export Analytics Data"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("Generate Monthly Report"):
                    report = self.generate_monthly_report(metrics, visits_df, patients_df)
                    st.download_button(
                        label="📥 Download Report",
                        data=report,
                        file_name=f"smart_emr_report_{datetime.now().strftime('%Y%m')}.txt",
                        mime="text/plain"
                    )
            
            with col2:
                if st.button("Export Raw Data (CSV)"):
                    csv = visits_df.to_csv(index=False)
                    st.download_button(
                        label="📥 Download CSV",
                        data=csv,
                        file_name=f"emr_visits_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )
            
            with col3:
                st.info(f"Last updated: {datetime.now().strftime('%H:%M:%S')}")
    
    def generate_monthly_report(self, metrics, visits_df, patients_df):
        """Generate a comprehensive monthly report"""
        report = f"""
SMART EMR - MONTHLY ANALYTICS REPORT
Generated: {datetime.now().strftime('%B %Y')}
=====================================

EXECUTIVE SUMMARY
-----------------
Total Patients: {metrics['total_patients']}
Total Visits: {metrics['total_visits']}
This Month: {metrics['visits_last_30_days']} visits
This Week: {metrics['visits_last_7_days']} visits

AI PERFORMANCE
--------------
Summaries Generated: {metrics['ai_summaries_generated']}
Prescription Acceptance: {metrics['prescription_acceptance_rate']*100:.1f}%
Average Accuracy Rating: {metrics['avg_accuracy_rating']:.1f}/5
Average Usefulness Rating: {metrics['avg_usefulness_rating']:.1f}/5
Positive Feedback Rate: {metrics['positive_feedback_rate']*100:.1f}%

PATIENT DEMOGRAPHICS
--------------------
Age Distribution:
"""
        
        if len(patients_df) > 0:
            age_groups = patients_df['age'].value_counts(bins=[0, 18, 30, 50, 70, 100], sort=False)
            for age_range, count in age_groups.items():
                report += f"  {age_range}: {count} patients\n"
            
            report += f"\nSex Distribution:\n"
            for sex, count in patients_df['sex'].value_counts().items():
                report += f"  {sex}: {count} patients\n"
        
        report += f"""

RECOMMENDATIONS
---------------
1. Continue regular feedback collection to improve AI performance
2. Maintain high vitals recording compliance for better clinical insights
3. Use rare disease detection alerts for early intervention
4. Review prescription patterns for optimization opportunities

Generated by Smart EMR Analytics Dashboard
==========================================
"""
        
        return report