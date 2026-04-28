import React from 'react';
import styles from './ScreenshotViewer.module.css';

interface ScreenshotViewerProps {
  image: string;
}

const ScreenshotViewer: React.FC<ScreenshotViewerProps> = ({ image }) => {
  return (
    <div className={styles.viewer}>
      <img
        src={image}
        alt="Screenshot"
        className={styles.image}
      />
      <div className={styles.meta}>
        <small>Last screenshot - Click to view full size</small>
      </div>
    </div>
  );
};

export default ScreenshotViewer;
