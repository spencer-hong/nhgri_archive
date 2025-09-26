import React, { Component } from 'react';
import { Container, Typography, Box } from "@material-ui/core";
import './App.css';
import ActionTable from './actionTable';

// Footer component for disclaimer
const Footer: React.FC = () => (
    <footer style={footerStyles}>
        <Typography variant="body2">
            <strong>Disclaimer:</strong> Tiramisu is built for the NHGRI Core Collection. Please refer to our manuscript and documentation for more information on the broader technical platform.
        </Typography>
        <Typography variant="body2">
            &copy; 2025 Born-Physical, Studied Digitally Consortium. All rights reserved.
        </Typography>
    </footer>
);

const footerStyles: React.CSSProperties = {
    position: "fixed",
    bottom: 0,
    left: 0,
    width: "100%",
    background: "#282c34",
    padding: "1rem",
    textAlign: "center",
    color: "white"
};

// App component
interface AppProps {}
interface AppState {}

export default class App extends Component<AppProps, AppState> {
    render() {
        return (
            <div className="App" style={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
                <header className="App-header">
                    Tiramisu Actions
                </header>

                <main className="App-content" style={{ flex: 1, paddingBottom: '80px' }}>
                    <Container maxWidth={false}>
                        <ActionTable />
                        <Box mt={4} p={2} style={docSectionStyles}>
                            <Typography variant="h6" gutterBottom>
                                Documentation
                            </Typography>
                            <Typography variant="body1">
                                Tiramisu Actions is a simple way to submit "jobs" to the Tiramisu task scheduler. More actions can be added by modifying the front-end source code in the Docker system.
                            </Typography>
                            <Typography variant="body1" style={{ marginTop: '10px' }}>
                                Before running any actions above, please make sure that your <span style={{ color: 'maroon' }}>core/tiramisu.env</span> and <span style={{ color: 'maroon' }}>core/.env</span> configuration files are properly set. For more information, refer to the Tiramisu-specific README.
                            </Typography>
                            <Typography variant="body1" style={{ marginTop: '10px' }}>
                                After clicking (only once) each action, please use the Tiramisu-provided Flower dashboard (<a href="http://localhost:8080/flower/dashboard" style={{ color: 'blue' }}>http://localhost:8080/flower/dashboard</a>) to check that <span style={{ color: 'maroon' }}>digest</span> action has finished before running <span style={{ color: 'maroon' }}>process</span>.
                            </Typography>
                            <Typography variant="body1" style={{ marginTop: '10px' }}>
                              Please follow the <span style={{ color: 'maroon' }}>start_here.ipynb</span> to understand how to use each of these actions.
                            </Typography>
                        </Box>
                    </Container>
                </main>

                <Footer />
            </div>
        );
    }
}

// Documentation section styling
const docSectionStyles: React.CSSProperties = {
    backgroundColor: '#f4f4f9',
    borderRadius: '8px',
    boxShadow: '0 2px 4px rgba(0, 0, 0, 0.1)',
    padding: '16px',
    marginTop: '20px',
};
